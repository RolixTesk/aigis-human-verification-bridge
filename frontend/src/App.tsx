import { useState } from 'react'

import { HumanVerificationModal } from './HumanVerificationModal'
import type { HumanVerificationChallenge, HumanVerificationResult } from './types'

interface ProofAccepted {
  status: 'proof_ready'
  encoded_length: number
  proof_sha256: string
  server_only: true
}
async function parsed<T>(response: Response): Promise<T> {
  if (response.ok) return response.json() as Promise<T>
  let message = `请求失败：HTTP ${response.status}`
  try {
    const body = await response.json() as { detail?: string }
    if (body.detail) message = body.detail
  } catch { /* stable fallback */ }
  throw new Error(message)
}

export default function App() {
  const [consent, setConsent] = useState(false)
  const [challenge, setChallenge] = useState<HumanVerificationChallenge | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<ProofAccepted | null>(null)

  async function start(version: 'gt3' | 'gt4') {
    if (!consent || loading) return
    setLoading(true); setError(''); setResult(null)
    try {
      setChallenge(await parsed<HumanVerificationChallenge>(await fetch('/api/demo/challenges', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ version }),
      })))
    } catch (reason) { setError(reason instanceof Error ? reason.message : '无法创建演示 challenge。') }
    finally { setLoading(false) }
  }

  async function complete(proof: HumanVerificationResult) {
    if (!challenge || loading) return
    setLoading(true); setError('')
    try {
      const accepted = await parsed<ProofAccepted>(await fetch(`/api/demo/challenges/${encodeURIComponent(challenge.challenge_id)}/complete`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(proof),
      }))
      setChallenge(null)
      setResult(accepted)
    } catch (reason) { setChallenge(null); setError(reason instanceof Error ? reason.message : '验证结果未被接受。') }
    finally { setLoading(false) }
  }

  async function cancel() {
    const current = challenge
    setChallenge(null)
    if (!current) return
    try { await fetch(`/api/demo/challenges/${encodeURIComponent(current.challenge_id)}`, { method: 'DELETE' }) }
    catch { setError('无法取消演示 challenge。') }
  }

  function changeConsent(next: boolean) {
    setConsent(next)
    if (!next && challenge) void cancel()
  }

  return <main className="shell">
    <section className="intro">
      <p className="kicker">AIGIS / GEETEST · HUMAN IN THE LOOP</p>
      <h1>把真人验证留给真人。</h1>
      <p>这是一个可移植的 Aigis challenge 与 GeeTest GT3/GT4 桥接示例。它负责展示官方组件并把严格校验的结果交回服务端，不自动操作或绕过验证。</p>
    </section>
    <section className="demo-card">
      <span className="mode">{import.meta.env.MODE === 'mock' ? 'MOCK SDK' : 'OFFICIAL SDK'}</span>
      <h2>独立演示</h2>
      <p>Mock 模式无需账号或网络，仅用于验证状态机。生产模式必须使用真实上游返回的 challenge。</p>
      <label className="consent"><input type="checkbox" checked={consent} onChange={(event) => changeConsent(event.target.checked)} /><span>我同意启动本次第三方真人验证组件。</span></label>
      <div className="actions">
        <button type="button" disabled={!consent || loading} onClick={() => start('gt3')}>生成 GT3 演示</button>
        <button type="button" disabled={!consent || loading} onClick={() => start('gt4')}>生成 GT4 演示</button>
      </div>
      {error && <p className="error">{error}</p>}
      {result && <div className="result"><strong>服务端已生成 Aigis 值</strong><span>长度 {result.encoded_length} · 摘要 {result.proof_sha256.slice(0, 16)}…</span><small>完整值只存在于服务端，本演示不会返回浏览器。</small></div>}
      <p className="privacy">真实组件可能处理网络、浏览器、操作系统和操作行为数据。集成方应在加载前取得授权并提供适用的隐私告知。</p>
    </section>
    {challenge && <HumanVerificationModal challenge={challenge} submitting={loading} onComplete={complete} onCancel={cancel} />}
  </main>
}
