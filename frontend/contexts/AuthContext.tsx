'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface AuthContextType {
  userId: string | null
  isLoggedIn: boolean
  login: (userId: string) => void
  logout: () => void
  setUserId: (userId: string | null) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserIdState] = useState<string | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  // Load from localStorage on mount
  useEffect(() => {
    const storedUserId = localStorage.getItem('user_id')
    if (storedUserId) {
      setUserIdState(storedUserId)
      setIsLoggedIn(true)
    }
  }, [])

  const login = (newUserId: string) => {
    localStorage.setItem('user_id', newUserId)
    setUserIdState(newUserId)
    setIsLoggedIn(true)
  }

  const logout = () => {
    localStorage.removeItem('user_id')
    setUserIdState(null)
    setIsLoggedIn(false)
  }

  const setUserId = (newUserId: string | null) => {
    if (newUserId) {
      localStorage.setItem('user_id', newUserId)
      setUserIdState(newUserId)
      setIsLoggedIn(true)
    } else {
      logout()
    }
  }

  return (
    <AuthContext.Provider
      value={{
        userId,
        isLoggedIn,
        login,
        logout,
        setUserId,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
