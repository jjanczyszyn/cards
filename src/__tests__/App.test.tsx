import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../App'

beforeEach(() => {
  // Mock fetch to return an empty index
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ decks: [] }),
  } as Response)
})

describe('App', () => {
  it('renders the title', async () => {
    render(<App />)
    expect(screen.getByText('Cards')).toBeInTheDocument()
  })

  it('renders the language toggle', () => {
    render(<App />)
    expect(screen.getByText('ES')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(<App />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
})
