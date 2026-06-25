<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: education.articles.0001-the-next-ai-advantage-is-evidence.article
  version: 1
  status: active
  layer: 04.education
  domain: education
  disciplines:
  - agentic
  kind: guide
  purpose: Document The Answer Has To Stand Up.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: education.readme
    path: .agentic/education/README.md
-->
# The Answer Has To Stand Up

KPMG published a report called *Redefining excellence in the age of agentic
AI*. It was the sort of thing that arrives wearing institutional authority:
global consulting firm, confident title, case studies about UBS, the NHS,
Swiss Federal Railways, and Transport for London, plus a list of citations to
make the whole thing look anchored.

Then the anchors started coming loose.

The report itself no longer appears to be publicly available from KPMG; the
public trail now runs through reporting about it. The
[Financial Times reported](https://www.ft.com/content/b3828e92-4961-4b39-84f0-c42f33be3c3f)
that the report contained false claims about how those organizations were
using AI, and that KPMG pulled the report from some of its websites while it
investigated. [TechRadar, summarizing GPTZero's work](https://www.techradar.com/pro/a-major-kpmg-report-on-ai-was-found-to-be-chock-full-of-ai-hallucinations),
reported that only five of the report's 45 citations accurately pointed to
real sources.

That is not a typo. It is not a small formatting mistake hiding in the
footnotes. It is a report about AI excellence becoming evidence for the
problem it was meant to explain.

That is the uncomfortable bit. The failure did not arrive looking like failure.
It arrived looking like work.

You can see versions of the same shape all over the place now. A passenger
asked an airline chatbot about a bereavement fare, followed the answer, and
later had to argue that the company was responsible for what its own chatbot
had told him. The tribunal agreed; the airline's attempt to treat the chatbot
as if it were some independent operator loose on the website was,
[in the adjudicator's word](https://www.businessinsider.com/airline-ordered-to-compensate-passenger-misled-by-chatbot-2024-2),
"remarkable."

Meeting notes have their own quieter version. The AI recap arrives five
minutes after the call, tidier than anything a human would have written while
also paying attention. This is genuinely attractive. Meetings are where
attention goes to discover whether it can die. But researchers looking at
[LLM-powered meeting recaps](https://arxiv.org/abs/2307.15793) found that
different recap forms serve different needs, and that people still edit,
delete, and argue with the recap because the summary is not the meeting.
Another paper on [meeting-summary errors](https://arxiv.org/abs/2407.11919)
describes omissions, irrelevance, and hallucination. In ordinary office terms:
someone can leave a call, open the recap, and find that the neat little action
item has made the wrong person responsible for the wrong thing.

Lawyers have managed the louder version, which is always kind of them. In
[Mata v. Avianca](https://en.wikipedia.org/wiki/Mata_v._Avianca%2C_Inc),
lawyers submitted legal filings with fake cases produced by ChatGPT. The comic
surface is easy enough. Lawyers, fake cases, judge unhappy. Lovely. But the
real point is less funny: the document had the form of a legal argument before
it had the substance of one.

That is the pattern hiding under the noise. Not "AI makes mistakes," which is
true and not especially new. The more dangerous pattern is that AI can give
weak work the posture of strong work. It can make a claim look cited, a
decision look settled, a meeting look aligned, a customer answer look official,
and a report look ready to circulate.

And the better AI gets at polish, the more expensive that posture becomes.

I ran into a smaller, less public version of this while working on the rules
around my own AI assistant.

The job sounded dry, because most jobs worth doing eventually find a way to
sound dry. Before I marked a piece of work finished, I wanted the assistant to
pause and ask whether any decisions from the conversation needed to be saved
for later. If I had changed direction, rejected an option, or created a rule I
would otherwise have to rediscover in three weeks, the assistant should catch
that.

In software, there is a stiff little name for this kind of note: an
architecture decision record. Ignore the phrase for a second. The ordinary
need is simple. Some decisions should not have to be reverse-engineered from
the finished thing. If the reason matters later, catch it while the reason is
still warm.

So far, so sensible.

Then I asked the question that ruins a surprising number of sensible ideas:
what would the assistant actually know?

The answer was: not enough.

The session record knew the work had started. It knew a branch had been
created. It knew a note for the session existed. That was not nothing, but it
was nowhere near enough to judge whether a decision was worth saving. It did
not reliably preserve the question I had asked, the issue that changed the
plan, the option we rejected, or the reason the change mattered.

In other words, I was about to ask the assistant to produce a mature-looking
judgment from an immature record.

That is the consulting-report problem in miniature. That is the chatbot problem
in miniature. That is the meeting-recap problem in miniature. The object looks
calm. The trail underneath it is missing.

The repair was not glamorous. It was not a new model, a clever prompt, or a
dramatic agentic flourish. It was making the work leave better tracks while it
was happening.

The session log had to capture the initial intent. It had to preserve the
questions asked, the issues raised, the decisions made, and the reason those
decisions mattered. It had to record what changed before the change was
finished. When a decision affected how the system worked, it needed a short
durable explanation: what changed, why it changed, and what future-me should
not have to guess.

Then the logs needed to become more than isolated chats. They had to group by
day. They had to show readable duration. They had to estimate token use, not
because tokens deserve reverence, but because repeated AI work has a
shape. Some sessions are quick assists. Some are long arguments with yourself
through a machine. Some keep circling the same decision because nobody made
the earlier answer durable.

That is when the work starts to compound. A conversation becomes a record. A
record becomes a decision note. A cluster of sessions becomes a pattern. A
pattern becomes a better way of working next time.

This is why "show your work" is too small a frame. It sounds like school, and
school has already done enough reputational damage to perfectly good ideas.

The standard I want is closer to this: the answer has to stand up.

If an AI-written customer response is going to tell someone what they can
claim, it needs to know where that answer came from. If a meeting recap is
going to assign work, it needs to preserve enough of the disagreement that the
team can correct it. If a report is going to carry citations, those citations
need to exist and support the claim being made. If my assistant is going to
say a decision should be saved, it needs a record rich enough to know what was
decided.

There is a temptation to treat this as a brake on speed. I think that gets it
backwards. Evidence is what lets speed survive contact with another person.

A polished answer is pleasant when everyone is in the room and still remembers
the messy conversation that produced it. The test comes later, when the answer
travels. It gets forwarded. It gets quoted. It gets turned into a plan, a
promise, a ticket, a policy, a slide, a decision.

At that point, the impressive part is not that AI helped produce it.

The impressive part is that the work can still explain what it is standing on.
