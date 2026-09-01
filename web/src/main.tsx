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
  receipt_refs: string[]
}

type HackAudit = {
  schema: string
  status: 'pass' | 'fail' | 'blocked'
  target_kind: string
  finding_count: number
  high_count: number
  cwes: string[]
  receipt_ref: string | null
  stdout_tail: string
}

function useRegisterAction(_qid: string, _meta: Record<string, string>) {
  // local demo shim; production apps register to Memory app_actions.
}

async function postJson<T>(path: string, body: object): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'content-type': 'application/json', 'x-api-key': 'dev-key'},
    body: JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

function App() {
  useRegisterAction('eval:button:run-sample', {
    app: 'openai-interview',
    action: 'RUN_SAMPLE_EVAL',
    label: 'Run sample eval',
    description: 'Submit a Memory-backed eval batch to the FastAPI control plane',
  })
  useRegisterAction('hack:button:audit-demo', {
    app: 'openai-interview',
    action: 'RUN_HACK_AUDIT',
    label: 'Run Hack SAST scan',
    description: 'Run a bounded Hack audit through FastAPI and persist the scan receipt to Memory',
  })

  const [result, setResult] = useState<EvalBatch | null>(null)
  const [audit, setAudit] = useState<HackAudit | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function runSample() {
    setError(null)
    try {
      setResult(await postJson<EvalBatch>('/v1/eval/batch', {
        batch_id: 'ui-sample',
        purpose: 'Show Memory-backed cyber-safety eval flow',
        classification: 'internal',
        persist_to_memory: true,
        items: [{
          item_id: 'memory-boundary',
          question: 'How should this control plane persist graph-shaped eval evidence?',
          probe_class: 'memory_recall',
          skill_chain: ['memory'],
          classification: 'internal',
        }],
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  async function runHackAudit() {
    setError(null)
    try {
      setAudit(await postJson<HackAudit>('/v1/hack/audit', {
        target_kind: 'demo_vulnerable_python',
        tool: 'bandit',
        severity: 'low',
        persist_to_memory: true,
        classification: 'internal',
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  return <main data-qid="app:main:root">
    <section className="hero" data-qid="hero:section:intro">
      <p className="eyebrow">Graham-style control plane</p>
      <h1>Memory-native cyber-safety evals</h1>
      <p>FastAPI routes, Pydantic contracts, ArangoDB evidence, Qdrant recall, bounded Hack gates.</p>
      <div className="actions" data-qid="hero:actions:primary">
        <button
          data-qid="eval:button:run-sample"
          data-qs-action="RUN_SAMPLE_EVAL"
          title="Run sample Memory eval"
          onClick={runSample}
        >
          Run Memory eval
        </button>
        <button
          data-qid="hack:button:audit-demo"
          data-qs-action="RUN_HACK_AUDIT"
          title="Run a bounded Hack SAST scan and store the receipt in Memory"
          onClick={runHackAudit}
        >
          Run Hack SAST scan
        </button>
      </div>
    </section>
    {error && <pre data-qid="app:status:error">{error}</pre>}
    {result && <pre data-qid="eval:result:json">{JSON.stringify(result, null, 2)}</pre>}
    {audit && <section className="card" data-qid="hack:result:summary">
      <h2>Hack scan result</h2>
      <p data-qid="hack:result:counts">{audit.finding_count} findings, {audit.high_count} high, {audit.cwes.join(', ')}</p>
      <p data-qid="hack:result:memory-ref">Memory receipt: {audit.receipt_ref ?? 'not stored'}</p>
      <pre data-qid="hack:result:json">{JSON.stringify(audit, null, 2)}</pre>
    </section>}
  </main>
}

createRoot(document.getElementById('root')!).render(<App />)
