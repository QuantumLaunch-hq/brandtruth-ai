/**
 * Component Tests for Landing Page
 * 
 * Tests the main landing page UI elements and interactions.
 */

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LandingPage from '../app/page'

describe('Landing Page', () => {
  describe('Navigation', () => {
    it('renders the BrandTruth logo and name', () => {
      render(<LandingPage />)
      
      // Multiple instances (nav + footer)
      const brandElements = screen.getAllByText('BrandTruth')
      expect(brandElements.length).toBeGreaterThan(0)
      expect(brandElements[0]).toBeInTheDocument()
    })

    it('renders navigation links', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Features')).toBeInTheDocument()
      expect(screen.getByText('How It Works')).toBeInTheDocument()
      expect(screen.getByText('Sentiment Monitor ✨')).toBeInTheDocument()
    })

    it('renders Launch Dashboard button', () => {
      render(<LandingPage />)
      
      const dashboardButtons = screen.getAllByText('Launch Dashboard')
      expect(dashboardButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Hero Section', () => {
    it('renders the main headline', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/Create ads that are/)).toBeInTheDocument()
      expect(screen.getByText('honest')).toBeInTheDocument()
      expect(screen.getByText('convert')).toBeInTheDocument()
    })

    it('renders the subheadline', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/BrandTruth extracts real claims/)).toBeInTheDocument()
    })

    it('renders Start Creating Ads CTA button', () => {
      render(<LandingPage />)
      
      const ctaButtons = screen.getAllByText('Start Creating Ads')
      expect(ctaButtons.length).toBeGreaterThan(0)
    })

    it('renders trust badges', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Compliance-first')).toBeInTheDocument()
      expect(screen.getByText('No hallucinations')).toBeInTheDocument()
      expect(screen.getByText('60-second campaigns')).toBeInTheDocument()
    })
  })

  describe('Sentiment Monitor Section (Unique Feature)', () => {
    it('renders unique feature badge', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/UNIQUE FEATURE/)).toBeInTheDocument()
      expect(screen.getByText(/No Competitor Has This/)).toBeInTheDocument()
    })

    it('renders auto-pause headline', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/Ads that pause themselves during crises/)).toBeInTheDocument()
    })

    it('renders Try Sentiment Monitor button', () => {
      render(<LandingPage />)
      
      const sentimentButtons = screen.getAllByText('Try Sentiment Monitor')
      expect(sentimentButtons.length).toBeGreaterThan(0)
    })

    it('renders Auto-Pause Triggered demo', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Auto-Pause Triggered')).toBeInTheDocument()
      expect(screen.getByText('Negative sentiment detected')).toBeInTheDocument()
    })
  })

  describe('Features Section', () => {
    it('renders features section heading', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/Everything you need to create honest ads/)).toBeInTheDocument()
    })

    it('renders all four feature cards', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Brand Extraction')).toBeInTheDocument()
      expect(screen.getByText('Claim Verification')).toBeInTheDocument()
      expect(screen.getByText('Smart Image Matching')).toBeInTheDocument()
      expect(screen.getByText('One-Click Export')).toBeInTheDocument()
    })
  })

  describe('How It Works Section', () => {
    it('renders how it works heading', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/From URL to ads in 60 seconds/)).toBeInTheDocument()
    })

    it('renders all three steps', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Enter Your URL')).toBeInTheDocument()
      expect(screen.getByText('Review & Approve')).toBeInTheDocument()
      expect(screen.getByText('Export & Launch')).toBeInTheDocument()
    })
  })

  describe('Stats Section', () => {
    it('renders all statistics', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('60s')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument()
      expect(screen.getByText('3x')).toBeInTheDocument()
    })

    it('renders stat labels', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Average campaign time')).toBeInTheDocument()
      expect(screen.getByText('Compliance rate')).toBeInTheDocument()
      expect(screen.getByText('Hallucinated claims')).toBeInTheDocument()
      expect(screen.getByText('Faster than manual')).toBeInTheDocument()
    })
  })

  describe('Footer', () => {
    it('renders copyright notice', () => {
      render(<LandingPage />)
      
      expect(screen.getByText(/© 2025 BrandTruth AI/)).toBeInTheDocument()
    })

    it('renders footer navigation links', () => {
      render(<LandingPage />)
      
      // Footer has Dashboard and Sentiment Monitor links
      const footerLinks = screen.getAllByRole('link')
      expect(footerLinks.length).toBeGreaterThan(0)
    })
  })

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<LandingPage />)
      
      // Main h1 should exist
      const h1 = screen.getByRole('heading', { level: 1 })
      expect(h1).toBeInTheDocument()
      
      // Multiple h2s for sections
      const h2s = screen.getAllByRole('heading', { level: 2 })
      expect(h2s.length).toBeGreaterThan(0)
    })

    it('all links have href attributes', () => {
      render(<LandingPage />)
      
      const links = screen.getAllByRole('link')
      links.forEach(link => {
        expect(link).toHaveAttribute('href')
      })
    })

    it('buttons are keyboard accessible', async () => {
      render(<LandingPage />)
      const user = userEvent.setup()
      
      // Tab to first interactive element
      await user.tab()
      
      // Should be able to focus on elements
      expect(document.activeElement).not.toBe(document.body)
    })
  })

  describe('Demo Ad Cards', () => {
    it('renders sample ad cards in hero', () => {
      render(<LandingPage />)
      
      expect(screen.getByText('Stop Getting Rejected by ATS')).toBeInTheDocument()
      expect(screen.getByText('Your Career, Rewritten Smart')).toBeInTheDocument()
      expect(screen.getByText('AI-Powered Career Intelligence')).toBeInTheDocument()
    })

    it('shows Compliant badge on ad cards', () => {
      render(<LandingPage />)
      
      const compliantBadges = screen.getAllByText('Compliant')
      expect(compliantBadges.length).toBe(3)
    })
  })
})
