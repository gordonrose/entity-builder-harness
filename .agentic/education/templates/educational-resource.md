<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.templates.educational-resource
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: template
  purpose: Document Educational Resource.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# Educational Resource

## Metadata

- Type:
- Title:
- Audience:
- Source material:
- Profiles used:
- References used:

## Source Evidence

List the concrete log entries, decisions, or repo artifacts that ground this
resource.

## Resource

Draft the selected resource here.

For public-facing articles, first include or link an approved
`article-source-packet.md` and scene cards. Do not draft if the source packet
is insufficient. Then include or link an approved `article-editor-brief.md`. Do
not draft if the brief blocks the candidate. Then include or link an approved
`article-opening-lab.md`. Use the Article Writer Agent for the draft and return
the result to the Article Editor Agent before treating it as publishable. Store
writer notes and editor reviews beside the article, not inside the public
article body.

For talks, include:

- title
- thesis
- audience promise
- slide list
- timing plan
- script by slide
- audience interaction moments
- visual or demo suggestions
- humor moments
- strong closing

For lesson plans, use `lesson-plan.md` and include:

- 30-minute core
- 50-minute extension
- learning outcomes
- lesson arc
- facilitator script
- materials
- participant activity
- worked example
- debrief guide

For short public articles, include:

- title
- source packet summary
- scene card summary
- article editor brief summary
- article opening lab summary
- article calibration report summary, when user feedback or a user-final
  rewrite produced reusable lessons
- source scene used
- article body only
- alternate titles
- possible stronger endings
- opening audit
- source material density audit
- voice sample bank audit
- quality rubric score

## Teaching Notes

- What this teaches:
- What not to over-explain:
- Common misconception:
- Classroom use:

## Revision Notes

- What works:
- What may sound unlike the author:
- What to revise after feedback:

## Audits

### Specificity Audit

- Which concrete evidence supports this?
- Could this have been written without reading the logs?
- Is there a real incident, tradeoff, mistake, or surprise?
- Has the draft preserved the strongest source story, or reduced it to a weaker
  abstract lesson?
- Does the article contain details that could only come from the source
  material?
- Is the main reader bridge sourced rather than invented?

### Voice Audit

- Which lines sound like the author?
- Which lines sound machine-authored?
- Which lines are too polished?
- Which jokes feel forced?
- Which lines match the voice sample bank?
- Which lines sound like generic thoughtful AI commentary?

### Opening Audit

- Does the opening sound like a person talking to another person?
- Does it begin with a lived situation rather than an abstract thesis?
- Is the opening based on a concrete source scene from the brief?
- Does the scene contain visible motive, friction, and downside?
- Are the stakes felt within the first seven lines?
- Could a cold reader retell who is under pressure, what went missing or wrong,
  and what could happen because of it?
- Does the opening begin from human consequence rather than system mechanism?
- Does the opening avoid unexplained evaluative shortcuts like "useful",
  "obvious", "important", and "interesting"?
- Does the opening avoid calendar dates unless the exact date matters to the
  reader?
- Does the opening avoid fake vividness: metaphors that sound concrete but do
  not show a person, action, object, cost, or consequence?
- Does it reveal why the author cares without announcing that care directly?
- Does it give the reader a reason to care before internal vocabulary appears?
- Does it avoid punchy AI syntax and slogan-shaped contrast?
- Does it build the setting before using repo-specific examples or terms?
- Are jargon terms translated, delayed, or removed?

### Teaching Audit

- What will the audience understand afterward?
- Is the explanation accessible before it becomes abstract?
- Is there a classroom moment, example, or exercise?
