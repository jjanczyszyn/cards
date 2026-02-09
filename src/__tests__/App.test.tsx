import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../App'

describe('App', () => {
  it('renders the title', () => {
    render(<App />)
    expect(screen.getByText('Cards')).toBeInTheDocument()
  })

  it('renders the deck prompt', () => {
    render(<App />)
    expect(screen.getByText('Choose a deck to begin')).toBeInTheDocument()
  })
})
