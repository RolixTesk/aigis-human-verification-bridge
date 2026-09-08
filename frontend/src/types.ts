export interface HumanVerificationChallenge {
  challenge_id: string
  version: 'gt3' | 'gt4'
  captcha_id: string
  challenge: string | null
  success: number | null
  new_captcha: boolean | null
  risk_type: string | null
  user_info: string | null
  expires_at: string
}
export interface Gt3VerificationResult {
  version: 'gt3'
  geetest_challenge: string
  geetest_validate: string
  geetest_seccode: string
}

export interface Gt4VerificationResult {
  version: 'gt4'
  lot_number: string
  captcha_output: string
  pass_token: string
  gen_time: string
  captcha_id: string
  sign_token?: string
}

export type HumanVerificationResult = Gt3VerificationResult | Gt4VerificationResult

export interface GeetestCaptcha {
  appendTo(target: string | HTMLElement): GeetestCaptcha
  onReady(callback: () => void): GeetestCaptcha
  onSuccess(callback: () => void): GeetestCaptcha
  onClose(callback: () => void): GeetestCaptcha
  onError(callback: () => void): GeetestCaptcha
  getValidate(): Record<string, unknown> | false
  destroy?(): void
  showCaptcha?(): void
}

declare global {
  interface Window {
    initGeetest?: (config: Record<string, unknown>, callback: (captcha: GeetestCaptcha) => void) => void
    initGeetest4?: (config: Record<string, unknown>, callback: (captcha: GeetestCaptcha) => void) => void
  }
}
