<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence.reader-world-research-packet
  version: 1
  status: active
  layer: 05.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document Reader-World Research Packet.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Reader-World Research Packet

## Metadata

- Article candidate: The Answer Has To Stand Up
- Source packet: `source-packet.md`
- Researcher: Codex
- Research date: 2026-06-16
- Audience: hype-adjacent, non-technical or lightly technical AI readers
- Status: sufficient

## Search Scope

Reviewed public sources where non-specialist business readers can see AI work
moving into ordinary decisions:

- technology and business reporting on AI-generated reports, customer-service
  chatbots, legal filings, medical or workplace notes, and security reports
- arXiv papers on LLM meeting recaps, meeting-summary errors, and generated
  references
- public legal/news summaries of fake AI citations

These sources match the audience because they concern recognizable work
objects: reports, chatbots, meeting notes, court filings, customer answers,
and incident reports.

## Source Log

| Source | Link or local artifact | Artifact availability | Date checked | What reader-world pressure it reveals | Usable? |
|---|---|---|---:|---|---|
| Financial Times on KPMG report | https://www.ft.com/content/b3828e92-4961-4b39-84f0-c42f33be3c3f | Original KPMG report not directly linked; FT says KPMG pulled it from some websites while investigating | 2026-06-16 | Named organizations disputed the report's AI case studies, and KPMG pulled the report from some websites while investigating | yes |
| TechRadar on KPMG AI report hallucinations | https://www.techradar.com/pro/a-major-kpmg-report-on-ai-was-found-to-be-chock-full-of-ai-hallucinations | Secondary reporting on GPTZero's work; original KPMG report not directly linked | 2026-06-16 | A serious report can carry plausible-looking citations and case studies that do not hold up | yes |
| Business Insider on Air Canada chatbot tribunal | https://www.businessinsider.com/airline-ordered-to-compensate-passenger-misled-by-chatbot-2024-2 | Linked news report; underlying tribunal order available through public reporting | 2026-06-16 | A customer can rely on a chatbot answer and force the company to defend what its AI said | yes |
| Microsoft meeting recap research | https://arxiv.org/abs/2307.15793 | Direct paper link | 2026-06-16 | Meeting recaps are valuable but need context, editing, and consensus around what the recap means | yes |
| Meeting summary error research | https://arxiv.org/abs/2407.11919 | Direct paper link | 2026-06-16 | Meeting summaries can contain omission, irrelevance, hallucination, and structural errors | yes |
| Mata v. Avianca summary | https://en.wikipedia.org/wiki/Mata_v._Avianca%2C_Inc. | Public summary; use briefly and prefer primary legal sources before publication if central | 2026-06-16 | A formal filing can look legally complete while resting on fake cases | yes |
| Axios on polished but wrong AI outputs | https://www.axios.com/2026/05/30/ai-accuracy-chatbots-hallucinations | Linked news report | 2026-06-16 | The risk is not only error; it is error delivered in confident, polished language | yes |
| ChatGPT attribution paper | https://arxiv.org/abs/2309.09401 | Direct paper link | 2026-06-16 | Generated answers can appear attributed while the references do not exist or do not support the claim | yes |
| TechRadar on Cisco AI security reports | https://www.techradar.com/pro/security/cisco-tried-using-ai-to-write-security-incident-reports-and-things-didnt-really-go-as-planned | Linked news report | 2026-06-16 | AI-generated incident reports can be well received while still carrying inaccuracies, contamination, and inconsistent conclusions | yes |

## Artifact Availability

- KPMG report: no direct public KPMG link found during research. The article
  should say the report itself no longer appears publicly available from KPMG
  and should route readers through the Financial Times and TechRadar reporting.
- GPTZero analysis: used through TechRadar's summary unless a primary GPTZero
  source is found before publication.
- Other supporting sources: direct public links exist, though central claims
  should be rechecked before publication.

## Scene Seeds

### Seed 1

- Source: Financial Times and TechRadar on KPMG report
- Who is involved: consulting firm, report readers, named organizations,
  downstream media or business readers
- What work product exists: agentic AI report with citations and case studies
- What pressure is on it: the report is meant to carry institutional authority
- What exact object is in the room: a polished PDF/report with 45 citations
- Artifact availability: original report unavailable from KPMG during
  research; use FT and TechRadar links and say so explicitly
- What can go wrong: false claims travel because the report looks credible
- Why a non-technical reader would recognize it: everyone has trusted a report
  more because it looked official
- How it helps set the table: opens with a public, concrete failure of
  evidence beneath polish
- Reuse risk: fresh

### Seed 2

- Source: Business Insider on Air Canada chatbot
- Who is involved: passenger, airline, chatbot, tribunal
- What work product exists: chatbot answer about bereavement fares
- What pressure is on it: a customer makes a purchase decision during a
  stressful family situation
- What exact object is in the room: a chatbot answer and later email exchange
- What can go wrong: the company tries to disown a customer-facing AI answer
- Why a non-technical reader would recognize it: anyone can picture relying on
  a support answer and being told later it did not count
- How it helps set the table: shows AI output becoming a promise
- Reuse risk: fresh

### Seed 3

- Source: Microsoft meeting recap research
- Who is involved: meeting participants using AI recaps
- What work product exists: highlights, minutes, and action items
- What pressure is on it: post-meeting work depends on what people believe was
  agreed
- What exact object is in the room: meeting recap document
- What can go wrong: people edit/delete because the recap misses the context
  or shared meaning
- Why a non-technical reader would recognize it: every workplace has meetings
  whose notes become the supposed truth
- How it helps set the table: makes the article relatable before internal
  harness details
- Reuse risk: fresh

### Seed 4

- Source: Meeting summary error research
- Who is involved: people relying on generated meeting summaries
- What work product exists: automatically generated meeting summary
- What pressure is on it: summaries drive action, planning, and follow-up
- What exact object is in the room: summary with possible omission,
  irrelevance, hallucination, or structural error
- What can go wrong: the summary sounds coherent while losing what mattered
- Why a non-technical reader would recognize it: a neat summary can be wrong in
  ways that are tedious to catch
- How it helps set the table: shows why clean recaps need evidence and review
- Reuse risk: fresh

### Seed 5

- Source: Mata v. Avianca summary
- Who is involved: lawyers, judge, opposing counsel, client
- What work product exists: legal brief with fake cases
- What pressure is on it: the document must survive hostile review
- What exact object is in the room: court filing with citations
- What can go wrong: formal authority masks nonexistent support
- Why a non-technical reader would recognize it: fake citations are easy to
  understand even outside law
- How it helps set the table: illustrates the difference between form and
  substance
- Reuse risk: common example; use briefly, not as opener

### Seed 6

- Source: Axios on polished but wrong AI outputs
- Who is involved: professionals leaning on AI outputs
- What work product exists: polished answer, summary, note, or clinical draft
- What pressure is on it: people trust polished language when under time
  pressure
- What exact object is in the room: confident answer that may omit or misstate
  details
- What can go wrong: the saved time gets spent later on missed verification
- Why a non-technical reader would recognize it: the workplace already rewards
  clear-looking answers
- How it helps set the table: supports the article's confidence-versus-truth
  frame
- Reuse risk: fresh

### Seed 7

- Source: ChatGPT attribution paper
- Who is involved: people asking ChatGPT for answers with sources
- What work product exists: answer plus references
- What pressure is on it: citations make the answer feel checkable
- What exact object is in the room: generated source list
- What can go wrong: references may not exist or may not support the claim
- Why a non-technical reader would recognize it: citations carry social
  authority even when nobody checks them
- How it helps set the table: supports the report/citation argument
- Reuse risk: fresh

### Seed 8

- Source: TechRadar on Cisco AI security reports
- Who is involved: security teams testing AI-generated incident reports
- What work product exists: security incident report
- What pressure is on it: readers need accurate conclusions during risk
  response
- What exact object is in the room: generated report from source documents
- What can go wrong: inaccuracies, contamination, and inconsistent conclusions
  survive because the report reads well
- Why a non-technical reader would recognize it: every organization has
  reports that get trusted because they sound competent
- How it helps set the table: adds workplace-report texture beyond citations
- Reuse risk: fresh

## Reader Recognition Patterns

- Polished documents inherit authority from format: report, citation, court
  filing, incident report.
- AI answers can become promises when a customer or colleague acts on them.
- Meeting summaries can settle reality while quietly losing disagreement,
  context, or ownership.
- The danger is often not an absurd hallucination but a plausible answer that
  survives the first skim.
- The cost appears later, when someone must defend, correct, trust, or act on
  the output.

## Setting-The-Table Options

1. Open with KPMG report and citations, then move through customer chatbot and
   meeting recaps before naming the thesis.
   - Why it works: fresh, current, public, evidence-shaped.
   - Risk: could sound too media-commentary unless quickly bridged to ordinary
     work objects.

2. Open with Air Canada chatbot, then broaden to reports and meeting recaps.
   - Why it works: emotionally clear customer consequence.
   - Risk: customer-service story could pull the article away from workplace
     evidence.

3. Open with meeting recap and action item, then escalate to KPMG and legal
   filings.
   - Why it works: most relatable office setting.
   - Risk: opening may feel invented unless tied tightly to research.

Selected option: KPMG opening, because it makes evidence failure visible in an
AI-specific work product without reusing the author's prior anecdote. The
opening should name KPMG and attribute the claims to public reporting rather
than hiding behind "major consulting firm."

## Example Ledger Check

Checked: `docs/education/articles/example-ledger.md`.

The prior customer-worth-20%-of-revenue anecdote is retired as a major example
for this article. The rewrite uses KPMG as the opening example, Air Canada and
meeting recaps as supporting reader-world examples, and Mata v. Avianca as a
brief supporting example only.

## Line 30 Cold-Reader Gate

Status: pass.

- World: professional reports, customer answers, meeting notes, and formal
  documents being created or helped by AI.
- Person: a reader, customer, colleague, lawyer, or operator who has to rely on
  a clean-looking output.
- Object under pressure: report, chatbot answer, meeting recap, legal filing,
  incident report.
- AI temptation: speed, polish, authority, and reduced blank-page pain.
- Downside: weak work gains the posture of strong work and then travels.
- Personal relevance: the reader is likely already forwarding, reading, or
  relying on AI-shaped outputs.

## Missing Material

- A stronger exact before/after excerpt of the thin harness session record
  would still improve the second act.
- If the article goes to publication, source links should be checked again.

## Decision

Sufficient: proceed to rewrite and editor review.
