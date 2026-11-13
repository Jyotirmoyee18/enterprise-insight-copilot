"""
Content generation agent -- renders the insight agent's output into a
finished artifact.

Two modes:
  - `template_path` provided -> fills the user's own uploaded PPTX (adds a
    findings slide matching the existing slide master rather than a generic
    deck). Template-editing limitations of python-pptx (can't duplicate
    slides, formatting resets on text_frame.text=...) are handled by writing
    into existing placeholders / run-level text only.
  - No template -> builds a small standalone deck from scratch.

TTS narration is a stubbed integration point (Azure Speech) -- see
`_synthesize_narration_stub`.
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "reports"


async def run_content_agent(state: dict) -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    template_path = state.get("template_path")

    if template_path:
        output_path = _fill_template(state, template_path)
    else:
        output_path = _build_from_scratch(state)

    state["output_path"] = str(output_path)
    state["narration_path"] = _synthesize_narration_stub(state)
    return state


def _build_from_scratch(state: dict) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)

    _add_title_slide(prs, state)
    _add_kpi_slide(prs, state)
    if state.get("doc_result", {}).get("citations"):
        _add_contract_slide(prs, state)
    if state.get("vision_result", {}).get("detections"):
        _add_shelf_slide(prs, state)
    _add_insight_slide(prs, state)

    out = OUTPUT_DIR / f"report_{state.get('session_id', 'demo')}.pptx"
    prs.save(out)
    return out


def _fill_template(state: dict, template_path: str) -> Path:
    prs = Presentation(template_path)
    # Append a findings slide using the template's own layout so it matches
    # the deck's existing branding, rather than inserting a generic slide.
    layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    if slide.shapes.title:
        slide.shapes.title.text = "Copilot findings"
    body = _find_body_placeholder(slide)
    if body:
        tf = body.text_frame
        tf.text = state.get("insight", "")
    out = OUTPUT_DIR / f"report_{state.get('session_id', 'demo')}.pptx"
    prs.save(out)
    return out


def _find_body_placeholder(slide):
    for shape in slide.placeholders:
        if shape.placeholder_format.idx != 0:  # 0 is usually the title
            return shape
    return None


def _add_title_slide(prs, state):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Merchandising QBR — Copilot Draft"
    if len(slide.placeholders) > 1:
        slide.placeholders[1].text = state["user_query"]


def _add_kpi_slide(prs, state):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "KPI summary"
    body = _find_body_placeholder(slide)
    rows = state.get("sql_result", {}).get("rows", [])
    if body:
        tf = body.text_frame
        tf.text = "" if not rows else ""
        for i, r in enumerate(rows[:6]):
            line = (
                f"{r['region']} {r['quarter']}: ${r['revenue']:,.0f} revenue "
                f"({r['attainment_pct']}% of target, {r['yoy_or_qoq_flag']})"
            )
            if i == 0:
                tf.text = line
            else:
                p = tf.add_paragraph()
                p.text = line
                p.font.size = Pt(14)


def _add_contract_slide(prs, state):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Relevant contract terms"
    body = _find_body_placeholder(slide)
    citations = state.get("doc_result", {}).get("citations", [])
    if body and citations:
        tf = body.text_frame
        tf.text = f"[{citations[0]['doc_id']} p.{citations[0]['page']}] {citations[0]['text']}"
        for c in citations[1:3]:
            p = tf.add_paragraph()
            p.text = f"[{c['doc_id']} p.{c['page']}] {c['text']}"
            p.font.size = Pt(13)


def _add_shelf_slide(prs, state):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Shelf-audit findings"
    body = _find_body_placeholder(slide)
    vision = state.get("vision_result", {})
    if body:
        tf = body.text_frame
        tf.text = f"{vision.get('flagged_count', 0)} of {len(vision.get('detections', []))} audited images flagged"
        for d in vision.get("flagged", [])[:4]:
            p = tf.add_paragraph()
            issue = "out of stock" if d["out_of_stock_flag"] else "planogram violation"
            p.text = f"{d['image_ref']}: {issue} (confidence {d['confidence']})"
            p.font.size = Pt(13)


def _add_insight_slide(prs, state):
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Insight & recommended action"
    body = _find_body_placeholder(slide)
    if body:
        body.text_frame.text = state.get("insight", "")


def _synthesize_narration_stub(state: dict) -> str | None:
    """Integration point for Azure Speech Text-to-Speech. Not called live
    here (needs AZURE_SPEECH_KEY); returns None so callers can tell no audio
    was generated in this run."""
    from app.core.config import settings

    if not settings.azure_speech_key:
        return None
    raise NotImplementedError("Wire up azure.cognitiveservices.speech.SpeechSynthesizer here.")
