import { createContext, useContext, useEffect, useRef, useState } from 'react'
// @ts-ignore — hashconnect installed on Vercel; may not be in local node_modules
import { HashConnect } from 'hashconnect'

type WalletContextType = {
  isConnected: boolean
  accountId: string | null
  connectWallet: () => Promise<void>
  disconnectWallet: () => void
  loading: boolean
  error: string | null
}

const WalletContext = createContext<WalletContextType | null>(null)

export const WalletProvider = ({ children }: { children: React.ReactNode }) => {
  const hashConnect = useRef<HashConnect | null>(null)

  const [accountId, setAccountId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (typeof window === 'undefined') return

    // ✅ Correct: constructor takes NO arguments
    hashConnect.current = new HashConnect()
  }, [])

  const connectWallet = async () => {
    if (!hashConnect.current) return

    setLoading(true)
    setError(null)

    try {
      console.log('[HashPack] init()')

      const initData = await hashConnect.current.init({
        network: 'testnet',
        name: 'TruthForge',
        description: 'Verifiable Intelligence Layer for Global Trade',
        icon: `${window.location.origin}/favicon.png`
      })

      if (!initData.pairingString) {
        throw new Error('Pairing string not generated')
      }

      console.log('[HashPack] Opening extension')

      const result = await hashConnect.current.connectToLocalWallet(
        initData.pairingString
      )

      if (result?.accountIds?.length) {
        setAccountId(result.accountIds[0])
        console.log('[HashPack] Connected:', result.accountIds[0])
      } else {
        throw new Error('No account returned from HashPack')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wallet connection failed'
      console.error('[HashPack ERROR]', err)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const disconnectWallet = () => {
    setAccountId(null)
  }

  return (
    <WalletContext.Provider
      value={{
        isConnected: !!accountId,
        accountId,
        connectWallet,
        disconnectWallet,
        loading,
        error
      }}
    >
      {children}
    </WalletContext.Provider>
  )
}

export const useWallet = () => {
  const ctx = useContext(WalletContext)
  if (!ctx) throw new Error('useWallet must be used inside WalletProvider')
  return ctx
}
