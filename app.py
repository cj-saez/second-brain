import os, json
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.')
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# ── Full context injected into every Claude call ──────────────────────────────
CONTEXT = """
TODAY: Tuesday, April 29, 2026.

CONTACTS & RELATIONSHIP HISTORY:
- Cascade Industrial Services (Portfolio Company, Chicago IL): Q1 review Apr 20 — margin bridge flagged for follow-up with Sarah. Contract renewal with Rick Halverson, counter expected May 5. Gulf Coast expansion confirmed Mar 28.
- Mike Devereux (VP Operations, Cascade, Chicago IL): Comp deferred — equity structure concern flagged 3 times since March. Union contract clauses sent to legal Apr 6. Performance review Mar 18: exceeds expectations on execution, development gap cross-team. Base comp is 8% below market median. Sarah's Scenario B equity model (3-year cliff, 25% annual acceleration) is in Vault — he has NOT opened the link yet.
- Sarah Chen (CFO, Cascade, Chicago IL): Q2 board deck draft shared Apr 17, EBITDA bridge slide requested. Q1 at 94% of plan. Capex timeline pushed 60 days. She approved Scenario B for Mike's comp.
- Jennifer Ruiz (VP Sales Candidate, Dallas TX): Final round complete — panel consensus to extend offer. Sourced via Jake Wren referral. Offer deadline Friday Apr 30. Flight risk increases each day.
- Marietta Foods (Key Customer, 23% of revenue, Atlanta GA): QBR today 9:30 AM with Janet Brusser. NPS: 62 up from 48 in Q4. Three Q4 action items committed for Apr 30, still open. Contract renewal — requesting 90-day price hold. Janet emailed yesterday 5:32 PM: has responses on 2 of 3 items, third needs more time.
- Dan Kowalski (Plant Manager, Gary IN): Line 3 downtime flagged 6:14 AM today — ~8% April throughput reduction. March throughput hit record. Safety audit: zero violations, commendation issued.
- Karen Vance (Board Observer, Maven Capital, New York NY): Pressed on customer concentration at Q1 board call. No written response sent yet.
- Heartland Clean Co. (Acquisition Target, Des Moines IA): NDA executed Apr 14. Financial package arrived this morning — CIM + 36-month financials. $4.2M EBITDA confirmed. 6.1x preliminary ask ($25.6M). Seller motivated by family health, wants 90-day close. Management call to schedule within 10-business-day window.
- Rick Halverson (General Counsel, Cascade): Union contract review — three clauses escalated to external counsel. $40K budget approved. Gary lease renewal: recommending 5-year term.
- SaniPro (Key Customer, 18% of revenue, Louisville KY): RISK — evaluating second-source supplier per Apr 4 intel. No relationship call since. Procurement lead has 3-year tenure. MidWest Clean Services quoted them Q4 2025.
- Janet Brusser (VP Procurement, Marietta Foods, Atlanta GA): Contract call — 90-day price hold request. Three Q4 open items committed Apr 30.

VAULT DOCUMENTS:
1. margin-bridge-acquisition (Apr 3): $1.04M margin improvement over 24 months. Procurement consolidation $420K, headcount efficiency $280K, pricing $340K. Sensitivity: if Marietta renews flat, bridge narrows $180K.
2. customer-concentration-analysis (Mar 24): Top 3 customers = 52% of revenue. Marietta 23%, SaniPro 18%. Karen Vance action item outstanding. Gulf Coast expansion reduces Marietta to ~18% by 2028.
3. mike-devereux-comp-review (Mar 18): Exceeds expectations execution. Base 8% below market. Scenario B approved: 3-year cliff, 25% annual acceleration on performance.
4. heartland-customer-presentation (Mar 10): Used in Apr 7 management intro. Zero safety violations and throughput record featured. Pricing model held in appendix.
5. sanipro-intel-q1-summary (Feb 20): March check-in — satisfaction "strong," open to volume increase. MidWest Clean Services quoted Q4 2025. Second-source evaluation flagged Apr 4.
6. cascade-3-year-strategy (Feb 14): Revenue target $42M by 2028. Pillars: Gulf Coast expansion, VP Sales hire (Jennifer Ruiz), Heartland acquisition.
7. q1-2026-board-deck (Feb 9): EBITDA $2.8M vs $3.0M plan (94%). Revenue $7.8M vs $8.0M (97%). Gap: Line 3 maintenance. Karen Vance action item: written response on concentration risk.
8. vp-operations-hiring-brief (Jan 28): Market comp range $180–220K base + equity. Mike's current comp is below this range.
9. heartland-clean-co-overview (Jan 20): $4.2M EBITDA on ~$22M revenue. 74% recurring from municipal contracts. 6.1x ask, 90-day close target.
10. marietta-foods-account-history (Jan 12): NPS trend 41→48→48→62. Two Line 1 disruptions 2023, resolved without contract risk. Average annual price increase accepted: 3.2%.
11. tom-ridley-1-1-running-notes (Nov 2025): Former VP Sales departed Oct 2025. Marietta and SaniPro were his primary accounts. Three pipeline opportunities status unknown — for Jennifer to inherit.
12. union-contract-summary (Oct 2025): Gary IN facility. EXPIRES MAY 15, 2026 — 16 days away. Three clauses flagged by Rick Halverson conflicting with planned operational changes.

CALENDAR THIS WEEK:
- Tue Apr 29 (Today): Marietta QBR 9:30 AM (Janet Brusser), Dan Kowalski ops debrief 11:00 AM
- Wed Apr 30: Cascade Industries review 10:00 AM, Mike Devereux comp discussion 1:00 PM
- Thu May 1: Q2 board deck dry-run 2:00 PM (Sarah Chen)
- Fri May 2: Jennifer Ruiz offer review 3:30 PM

PRIORITY STACK:
1. HIGH — Mike comp conversation: Wed 1 PM. Scenario B ready. He hasn't opened the Vault link.
2. HIGH — Jennifer Ruiz offer: Friday EOD. Flight risk every day it sits.
3. HIGH — SaniPro check-in: This week. 18% of revenue. Second-source risk active.
4. MEDIUM — Get Dan's Line 3 numbers: Needed before Thursday dry-run.
5. MEDIUM — Close Marietta Q4 items: Janet committed for April 30.
6. LOW — Karen Vance written response: After Thursday dry-run.

FINANCIAL SNAPSHOT:
- Q1 EBITDA: $2.8M (94% of $3.0M plan)
- Q1 Revenue: $7.8M (97% of $8.0M plan)
- Active acquisition: Heartland — $4.2M EBITDA, $25.6M ask (6.1x)
- Union contract expires: May 15, 2026 (16 days from today)
- Customer concentration: Marietta 23%, SaniPro 18%, Heartland 11%
"""

SYSTEM_PROMPT = f"""You are Second Brain — an AI chief of staff and personal intelligence assistant. Today is Tuesday, April 29, 2026.

You have full, real-time context on the user's business: contacts, open deals, calendar, vault documents, and active priorities. Answer questions directly and specifically using this context. Be concise but substantive. Reference specific people, numbers, and dates. Sound like a brilliant, well-briefed chief of staff — not a generic AI assistant.

When drafting emails or communications, make them sharp and context-specific. When asked about people, reference their actual history. When asked about strategy, tie it to current priorities. When asked to prepare for a meeting, pull everything relevant.

{CONTEXT}"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'second-brain.html')


@app.route('/ask', methods=['POST'])
def ask():
    """Streaming chat endpoint. Accepts {message, history, prefs} and streams SSE."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])  # [{role, content}, ...]
    prefs = data.get('prefs', None)

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or not api_key.startswith('sk-'):
        def no_key():
            msg = "⚠️ No API key found. Add ANTHROPIC_API_KEY=sk-ant-... to your .env file and restart app.py."
            yield f"data: {json.dumps({'text': msg})}\n\n"
            yield "data: [DONE]\n\n"
        return Response(stream_with_context(no_key()), mimetype='text/event-stream')

    # Build personalization layer from onboarding prefs
    personalization = ''
    if prefs:
        name = prefs.get('name', 'the user')
        use_case = prefs.get('useCase', '')
        tracks = prefs.get('tracks', '')
        personalization = f"""

USER PROFILE (from onboarding):
- Name: {name}
- Role / use case: {use_case}
- Focus areas: {tracks}

Tailor your tone, priorities, and what you surface to match this profile. A CEO operating a portfolio company needs different emphasis than someone running a search fund. Adjust your framing, depth, and what you proactively flag based on their stated focus areas."""

    system = SYSTEM_PROMPT + personalization
    messages = history + [{'role': 'user', 'content': message}]

    def generate():
        try:
            with client.messages.stream(
                model='claude-sonnet-4-6',
                max_tokens=1500,
                system=system,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


if __name__ == '__main__':
    key_set = bool(os.environ.get('ANTHROPIC_API_KEY', '').startswith('sk-'))
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'✓' if key_set else '✗'} ANTHROPIC_API_KEY {'found' if key_set else 'not found — add it to .env'}")
    print(f"→ Second Brain running at http://localhost:{port}\n")
    app.run(debug=False, host='0.0.0.0', port=port)
