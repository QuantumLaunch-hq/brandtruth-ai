/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, whileHover, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
    button: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, whileHover, ...rest } = props;
      return <button {...rest}>{children}</button>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock fetch for API calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ hooks: [] }),
  })
) as jest.Mock;

import StudioPage from '../../app/studio/page';

describe('Studio Page - Premium Version', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Onboarding Flow', () => {
    it('shows welcome screen initially', () => {
      render(<StudioPage />);
      
      expect(screen.getByText('BrandTruth Studio')).toBeInTheDocument();
      expect(screen.getByText(/Extract real claims/)).toBeInTheDocument();
    });

    it('shows enter URL button', () => {
      render(<StudioPage />);
      
      expect(screen.getByText('Enter your website URL')).toBeInTheDocument();
    });

    it('shows skip option', () => {
      render(<StudioPage />);
      
      expect(screen.getByText('Skip for now')).toBeInTheDocument();
    });

    it('navigates to URL input step', () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Enter your website URL'));
      
      expect(screen.getByPlaceholderText('yoursite.com')).toBeInTheDocument();
    });

    it('shows back button in URL step', () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Enter your website URL'));
      
      expect(screen.getByText('Back')).toBeInTheDocument();
    });

    it('back button returns to welcome', () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Enter your website URL'));
      fireEvent.click(screen.getByText('Back'));
      
      expect(screen.getByText('BrandTruth Studio')).toBeInTheDocument();
    });

    it('shows example URLs', () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Enter your website URL'));
      
      expect(screen.getByText('careerfied.ai')).toBeInTheDocument();
      expect(screen.getByText('stripe.com')).toBeInTheDocument();
    });

    it('clicking example populates input', async () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Enter your website URL'));
      fireEvent.click(screen.getByText('careerfied.ai'));
      
      const input = screen.getByPlaceholderText('yoursite.com') as HTMLInputElement;
      expect(input.value).toBe('careerfied.ai');
    });

    it('skipping onboarding shows main studio', async () => {
      render(<StudioPage />);
      
      fireEvent.click(screen.getByText('Skip for now'));
      
      // Wait for state update
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
      });
    });
  });

  describe('Main Studio Interface', () => {
    beforeEach(async () => {
      render(<StudioPage />);
      fireEvent.click(screen.getByText('Skip for now'));
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
      });
    });

    it('shows chat input', () => {
      expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
    });

    it('shows command palette trigger', () => {
      expect(screen.getByText('Commands')).toBeInTheDocument();
      expect(screen.getByText('⌘K')).toBeInTheDocument();
    });

    it('shows Studio branding', () => {
      expect(screen.getByText('Studio')).toBeInTheDocument();
    });

    it('shows preview panel', () => {
      expect(screen.getByText('Preview')).toBeInTheDocument();
    });

    it('shows claims tab', () => {
      expect(screen.getByText('Claims')).toBeInTheDocument();
    });

    it('can type in input', async () => {
      jest.useRealTimers(); // userEvent needs real timers
      
      const input = screen.getByPlaceholderText('Ask anything...');
      await userEvent.type(input, 'Generate hooks');
      
      expect(input).toHaveValue('Generate hooks');
    });
  });

  describe('Command Palette', () => {
    beforeEach(async () => {
      render(<StudioPage />);
      fireEvent.click(screen.getByText('Skip for now'));
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
      });
    });

    it('opens when Commands button clicked', async () => {
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search commands...')).toBeInTheDocument();
      });
    });

    it('shows available commands', async () => {
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByText('Generate hooks')).toBeInTheDocument();
        expect(screen.getByText('New campaign')).toBeInTheDocument();
        expect(screen.getByText('Plan budget')).toBeInTheDocument();
      });
    });

    it('shows command descriptions', async () => {
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByText('Create scroll-stopping headlines')).toBeInTheDocument();
      });
    });

    it('can search commands', async () => {
      jest.useRealTimers();
      
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search commands...')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search commands...');
      await userEvent.type(searchInput, 'hook');
      
      expect(screen.getByText('Generate hooks')).toBeInTheDocument();
      expect(screen.queryByText('Plan budget')).not.toBeInTheDocument();
    });

    it('shows no results message when search has no matches', async () => {
      jest.useRealTimers();
      
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search commands...')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search commands...');
      await userEvent.type(searchInput, 'xyznonexistent');
      
      expect(screen.getByText('No commands found')).toBeInTheDocument();
    });

    it('closes on escape key', async () => {
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search commands...')).toBeInTheDocument();
      });
      
      fireEvent.keyDown(window, { key: 'Escape' });
      
      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search commands...')).not.toBeInTheDocument();
      });
    });

    it('shows keyboard hints', async () => {
      fireEvent.click(screen.getByText('Commands'));
      
      await waitFor(() => {
        expect(screen.getByText('↑↓ Navigate')).toBeInTheDocument();
        expect(screen.getByText('↵ Select')).toBeInTheDocument();
      });
    });
  });

  describe('Phone Preview', () => {
    beforeEach(async () => {
      render(<StudioPage />);
      fireEvent.click(screen.getByText('Skip for now'));
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
      });
    });

    it('shows phone time', () => {
      expect(screen.getByText('9:41')).toBeInTheDocument();
    });

    it('shows sponsored label', () => {
      expect(screen.getByText('Sponsored')).toBeInTheDocument();
    });

    it('shows Learn More CTA', () => {
      expect(screen.getByText('Learn More')).toBeInTheDocument();
    });
  });
});

describe('Studio - URL Processing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('shows loading state during URL processing', async () => {
    render(<StudioPage />);
    
    fireEvent.click(screen.getByText('Enter your website URL'));
    
    const input = screen.getByPlaceholderText('yoursite.com');
    fireEvent.change(input, { target: { value: 'careerfied.ai' } });
    
    fireEvent.click(screen.getByText('Continue'));
    
    // Advance timers to start loading
    act(() => {
      jest.advanceTimersByTime(100);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/careerfied.ai/)).toBeInTheDocument();
    });
  });

  it('shows review step after processing', async () => {
    render(<StudioPage />);
    
    fireEvent.click(screen.getByText('Enter your website URL'));
    fireEvent.click(screen.getByText('careerfied.ai'));
    fireEvent.click(screen.getByText('Continue'));
    
    // Advance all timers to complete processing
    await act(async () => {
      jest.advanceTimersByTime(5000);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Careerfied')).toBeInTheDocument();
    }, { timeout: 10000 });
  }, 15000);
});

describe('Studio - Accessibility', () => {
  beforeEach(async () => {
    render(<StudioPage />);
    fireEvent.click(screen.getByText('Skip for now'));
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
    });
  });

  it('input is focusable', () => {
    const input = screen.getByPlaceholderText('Ask anything...');
    input.focus();
    expect(document.activeElement).toBe(input);
  });

  it('buttons are keyboard accessible', () => {
    const commandsButton = screen.getByText('Commands').closest('button');
    expect(commandsButton).not.toBeNull();
  });
});
