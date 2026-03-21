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

    hashConnect.current = new HashConnect(
      'testnet',
      {
        name: 'TruthForge',
        description: 'Verifiable Intelligence Layer for Global Trade',
        icon: `${window.location.origin}/favicon.png`
      }
    )
  }, [])

  const connectWallet = async () => {
    if (!hashConnect.current) return

    setLoading(true)
    setError(null)

    try {
      console.log('Initializing HashConnect')

      const initData = await hashConnect.current.init()

      const pairingString = initData.pairingString
      if (!pairingString) {
        throw new Error('No pairing string generated')
      }

      console.log('Triggering HashPack extension popup')

      const result = await hashConnect.current.connectToLocalWallet(pairingString)

      if (result?.accountIds?.length) {
        setAccountId(result.accountIds[0])
      } else {
        throw new Error('No account returned from HashPack')
      }

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Wallet connection failed'
      console.error('HashPack connect error:', err)
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
