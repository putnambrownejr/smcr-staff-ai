# How To Use With ChatGPT

This repo works best today as a two-part setup:

1. ChatGPT helps you think, shape requests, and interpret results.
2. Your local `smcr-staff-ai` API does the actual execution and local storage.

That keeps costs low, avoids remote MCP hosting, and still gives you a useful planning workflow.

## Best Current Setup

### What ChatGPT does well

- Reads and understands the GitHub repo
- Helps choose the right route
- Builds request payloads
- Refines plans and products after you run them
- Helps turn outputs into better prompts, letters, FRAGOs, or action items

### What the local API does well

- Executes staff workflows
- Stores local handoffs, uploads, and actions
- Builds planning packages
- Preserves private user context

## What To Open

Keep these open side by side:

- ChatGPT with your GitHub repo connected
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Optional dashboard: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

## Best Front Door

If you only use one route, use:

- `POST /planning/staff-package`

That route is the best current front door for turning one training or event problem into:

- S-2 estimate when needed
- S-3 training plan
- S-4 support view
- S-6 comms view
- medical / CASEVAC considerations
- optional G-9 civil considerations
- staff round robin
- XO vet
- product package drafts

## Lowest-Friction Workflow

### 1. Ask ChatGPT to shape the problem

Use a prompt like:

```text
Use my smcr-staff-ai repo as context. Help me build the request body for /planning/staff-package.

I want an advisory reserve training package.

Context:
- Unit: Civil affairs company
- Event: One-day field training during drill weekend
- Location: Miami
- Goal: Build a realistic micro field event that improves planning, reporting, and civil reconnaissance readiness
- Constraints:
  - One field day
  - Distributed Marines
  - Travel required for some personnel
  - Limited equipment draw time
- Coordinating sections:
  - S-1
  - S-4
  - S-6
  - Medical
- Required outputs:
  - WARNO
  - FRAGO
  - AAR structure

Build a valid JSON request body that matches the repo schema.
```

### 2. Paste the JSON into Swagger

Go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), open `POST /planning/staff-package`, click `Try it out`, and paste the payload.

### 3. Run the route locally

Review the response for:

- recommended course of action
- commander decisions now
- top risks
- cuts and deferments
- execution framework
- staff reviews
- product package drafts

### 4. Bring the output back to ChatGPT if needed

Use prompts like:

```text
I ran /planning/staff-package in my smcr-staff-ai repo. Help me tighten the recommended COA and commander decisions so they sound more decisive.
```

```text
Take this planning output and turn it into a cleaner naval-letter-ready package, while preserving the human-review warnings.
```

## Copy-Paste Prompt Templates

### A. Route selection

```text
Use my smcr-staff-ai repo as context. I have a reserve planning problem. Tell me which route I should call first, and why.
```

### B. Payload generation

```text
Use my smcr-staff-ai repo as context. Build me a valid JSON body for /planning/staff-package based on this scenario:

[paste scenario]
```

### C. Output cleanup

```text
I already ran /planning/staff-package. Help me turn the result into:
- a cleaner recommended plan
- sharper commander decisions
- a more useful FRAGO scaffold
- action items worth promoting
```

### D. Staff follow-ons

```text
Based on this planning package, tell me which follow-on routes I should run next in smcr-staff-ai for:
- S-1 support
- S-2 refinement
- S-4 refinement
- S-6 refinement
- actions tracking
```

## Example Request Files

Use these as starting points:

- [drill_weekend_field_training.json](/C:/smcr-staff-ai/docs/examples/drill_weekend_field_training.json)
- [annual_training_coordination.json](/C:/smcr-staff-ai/docs/examples/annual_training_coordination.json)
- [range_event_support_package.json](/C:/smcr-staff-ai/docs/examples/range_event_support_package.json)

They are shaped for `POST /planning/staff-package`.

## What ChatGPT Will Not Do In This Setup

Without a hosted MCP or app surface, ChatGPT will not:

- directly call your localhost API
- automatically read your local private files
- mutate your local app state by itself

That is the tradeoff for staying free and low-maintenance.

## What Makes This Setup Work Anyway

The repo is already strong enough that ChatGPT can still be very useful as:

- a planning partner
- a payload builder
- a repo interpreter
- an output refiner

And your local API remains the execution and memory layer.

## Recommended Starting Pattern

If you are using this alone, the simplest reliable pattern is:

1. Think in ChatGPT
2. Execute in `/docs`
3. Refine in ChatGPT
4. Promote useful outputs into tracked actions

That gives you most of the value without hosting anything.
