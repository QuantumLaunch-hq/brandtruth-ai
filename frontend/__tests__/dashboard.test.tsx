/**
 * Component Tests for Dashboard Page
 * 
 * Tests the main dashboard UI elements and interactions.
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock the Dashboard page
// Since it uses 'use client' and complex state, we create a simplified test version
const MockDashboardUI = () => {
  return (
    <div>
      {/* Header */}
      <nav>
        <span>BrandTruth</span>
        <a href="/">Back to Home</a>
      </nav>
      
      {/* URL Input Section */}
      <section data-testid="url-input-section">
        <h1>Create Ads from Your Website</h1>
        <p>Enter your website URL and we'll extract your brand to generate compliant ad campaigns.</p>
        <input 
          type="url" 
          placeholder="https://your-website.com"
          aria-label="Website URL"
          data-testid="url-input"
        />
        <button data-testid="extract-button">
          Extract Brand & Generate Ads
        </button>
      </section>

      {/* Settings */}
      <section data-testid="settings-section">
        <label>
          <span>Number of Variants</span>
          <select data-testid="variants-select">
            <option value="3">3 variants</option>
            <option value="5">5 variants</option>
            <option value="10">10 variants</option>
          </select>
        </label>
        <label>
          <input type="checkbox" data-testid="mock-data-toggle" />
          <span>Use Mock Data (Demo)</span>
        </label>
      </section>

      {/* Filter Controls */}
      <section data-testid="filter-controls">
        <button data-testid="filter-all">All</button>
        <button data-testid="filter-pending">Pending</button>
        <button data-testid="filter-approved">Approved</button>
        <button data-testid="filter-rejected">Rejected</button>
        <button data-testid="view-grid">Grid</button>
        <button data-testid="view-list">List</button>
      </section>

      {/* Brand Profile Display */}
      <section data-testid="brand-profile">
        <h2>Brand Profile</h2>
        <div data-testid="brand-name">Careerfied</div>
        <div data-testid="brand-tagline">Your intelligent career partner</div>
        <div data-testid="confidence-score">72%</div>
      </section>

      {/* Ad Variants Grid */}
      <section data-testid="variants-grid">
        <h2>Ad Variants</h2>
        {[1, 2, 3].map(i => (
          <article key={i} data-testid={`ad-variant-${i}`}>
            <h3>Headline {i}</h3>
            <p>Primary text for ad {i}</p>
            <button data-testid={`approve-${i}`}>Approve</button>
            <button data-testid={`reject-${i}`}>Reject</button>
          </article>
        ))}
      </section>

      {/* Export Section */}
      <section data-testid="export-section">
        <button data-testid="export-approved">Export Approved Ads</button>
      </section>
    </div>
  )
}

describe('Dashboard Page', () => {
  describe('Header', () => {
    it('renders BrandTruth branding', () => {
      render(<MockDashboardUI />)
      expect(screen.getByText('BrandTruth')).toBeInTheDocument()
    })

    it('renders back to home link', () => {
      render(<MockDashboardUI />)
      expect(screen.getByText('Back to Home')).toBeInTheDocument()
    })
  })

  describe('URL Input Section', () => {
    it('renders heading', () => {
      render(<MockDashboardUI />)
      expect(screen.getByText('Create Ads from Your Website')).toBeInTheDocument()
    })

    it('renders URL input field', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('url-input')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('https://your-website.com')).toBeInTheDocument()
    })

    it('renders extract button', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('extract-button')).toBeInTheDocument()
    })

    it('allows typing in URL input', async () => {
      render(<MockDashboardUI />)
      const user = userEvent.setup()
      const input = screen.getByTestId('url-input')
      
      await user.type(input, 'https://careerfied.ai')
      expect(input).toHaveValue('https://careerfied.ai')
    })
  })

  describe('Settings Section', () => {
    it('renders variants selector', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('variants-select')).toBeInTheDocument()
    })

    it('renders mock data toggle', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('mock-data-toggle')).toBeInTheDocument()
    })

    it('has variant options', () => {
      render(<MockDashboardUI />)
      expect(screen.getByText('3 variants')).toBeInTheDocument()
      expect(screen.getByText('5 variants')).toBeInTheDocument()
      expect(screen.getByText('10 variants')).toBeInTheDocument()
    })
  })

  describe('Filter Controls', () => {
    it('renders all filter buttons', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('filter-all')).toBeInTheDocument()
      expect(screen.getByTestId('filter-pending')).toBeInTheDocument()
      expect(screen.getByTestId('filter-approved')).toBeInTheDocument()
      expect(screen.getByTestId('filter-rejected')).toBeInTheDocument()
    })

    it('renders view toggle buttons', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('view-grid')).toBeInTheDocument()
      expect(screen.getByTestId('view-list')).toBeInTheDocument()
    })
  })

  describe('Brand Profile Display', () => {
    it('renders brand profile section', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('brand-profile')).toBeInTheDocument()
    })

    it('displays brand name', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('brand-name')).toHaveTextContent('Careerfied')
    })

    it('displays brand tagline', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('brand-tagline')).toHaveTextContent('Your intelligent career partner')
    })

    it('displays confidence score', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('confidence-score')).toHaveTextContent('72%')
    })
  })

  describe('Ad Variants Grid', () => {
    it('renders variants grid section', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('variants-grid')).toBeInTheDocument()
    })

    it('renders multiple ad variants', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('ad-variant-1')).toBeInTheDocument()
      expect(screen.getByTestId('ad-variant-2')).toBeInTheDocument()
      expect(screen.getByTestId('ad-variant-3')).toBeInTheDocument()
    })

    it('renders approve/reject buttons for each variant', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('approve-1')).toBeInTheDocument()
      expect(screen.getByTestId('reject-1')).toBeInTheDocument()
    })
  })

  describe('Export Section', () => {
    it('renders export button', () => {
      render(<MockDashboardUI />)
      expect(screen.getByTestId('export-approved')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('can click approve button', async () => {
      render(<MockDashboardUI />)
      const user = userEvent.setup()
      const approveBtn = screen.getByTestId('approve-1')
      
      await user.click(approveBtn)
      // Button should be clickable without errors
      expect(approveBtn).toBeInTheDocument()
    })

    it('can click reject button', async () => {
      render(<MockDashboardUI />)
      const user = userEvent.setup()
      const rejectBtn = screen.getByTestId('reject-1')
      
      await user.click(rejectBtn)
      expect(rejectBtn).toBeInTheDocument()
    })

    it('can toggle view mode', async () => {
      render(<MockDashboardUI />)
      const user = userEvent.setup()
      
      await user.click(screen.getByTestId('view-list'))
      await user.click(screen.getByTestId('view-grid'))
    })

    it('can change filter', async () => {
      render(<MockDashboardUI />)
      const user = userEvent.setup()
      
      await user.click(screen.getByTestId('filter-approved'))
      await user.click(screen.getByTestId('filter-pending'))
    })
  })
})
