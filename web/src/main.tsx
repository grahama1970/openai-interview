import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type EvalResult = {
  item_id: string
  status: 'pass' | 'fail' | 'blocked'
  finding: string
  memory_refs: string[]
}

type EvalBatch = {
  schema: string
  batch_id: string
  status: 'pass' | 'fail' | 'blocked'
  results: EvalResult[]
}

function useRegisterAction(_qid: string, _meta: Record<string, string>) {
  // local demo shim; production apps register to Memory app_actions.
}

function App() {
  useRegisterAction('eval:button:run-sample', {
    app: 'openai-interview',
    action: 'RUN_SAMPLE_EVAL',
    label: 'Run sample eval',
    description: 'Submit a Memory-backed eval batch to the FastAPI control plane',
  })

  const [result, setResult] = useState<EvalBatch | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function runSample() {
    setError(null)
    const response = await fetch('/v1/eval/batch', {
      method: 'POST',
      headers: {'content-type': 'application/json', 'x-api-key': 'dev-key'},
      body: JSON.stringify({
        batch_id: 'ui-sample',
        purpose: 'Show Memory-backed cyber-safety eval flow',
        classification: 'internal',
        items: [{
          item_id: 'memory-boundary',
          question: 'How should this control plane persist graph-shaped eval evidence?',
          probe_class: 'memory_recall',
          skill_chain: ['memory'],
          classification: 'internal',
        }],
      }),
    })
    if (!response.ok) {
      setError(`HTTP ${response.status}`)
      return
    }
    setResult(await response.json())
  }

  return <main data-qid="app:main:root">
    <section className="hero" data-qid="hero:section:intro">
      <p className="eyebrow">Graham-style control plane</p>
      <h1>Memory-native cyber-safety evals</h1>
      <p>FastAPI routes, Pydantic contracts, ArangoDB evidence, Qdrant recall, bounded Hack gates.</p>
      <button
        data-qid="eval:button:run-sample"
        data-qs-action="RUN_SAMPLE_EVAL"
        title="Run sample Memory eval"
        onClick={runSample}
      >
        Run sample eval
      </button>
    </section>
    {error && <pre data-qid="eval:status:error">{error}</pre>}
    {result && <pre data-qid="eval:result:json">{JSON.stringify(result, null, 2)}</pre>}
  </main>
}

createRoot(document.getElementById('root')!).render(<App />)
