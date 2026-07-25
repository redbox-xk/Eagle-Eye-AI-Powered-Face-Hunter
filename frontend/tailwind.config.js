/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        aura: {
          bg:      '#050a12',
          surface: '#0a1628',
          panel:   '#0d1e35',
          border:  '#1a2744',
          accent:  '#00d4ff',
          accent2: '#7c3aed',
          accent3: '#10b981',
          warn:    '#f59e0b',
          danger:  '#ef4444',
          text:    '#e2e8f0',
          muted:   '#64748b',
          dim:     '#94a3b8',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        'glow-sm':    '0 0 8px rgba(0,212,255,0.2)',
        'glow':       '0 0 20px rgba(0,212,255,0.15)',
        'glow-lg':    '0 0 40px rgba(0,212,255,0.12)',
        'glow-green': '0 0 20px rgba(16,185,129,0.15)',
        'glow-purple':'0 0 20px rgba(124,58,237,0.15)',
        'inner-glow': 'inset 0 0 20px rgba(0,212,255,0.04)',
      },
      animation: {
        'pulse2':    'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer':   'shimmer 2s linear infinite',
        'scan':      'scan 3s ease-in-out infinite',
        'fade-in':   'fadeIn 0.3s ease-out both',
        'slide-up':  'slideUp 0.3s ease-out both',
        'glow-ping': 'glowPing 2s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        scan: {
          '0%, 100%': { opacity: '0.3' },
          '50%':       { opacity: '1'   },
        },
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)'   },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)'    },
        },
        glowPing: {
          '0%, 100%': { boxShadow: '0 0 4px rgba(0,212,255,0.4)' },
          '50%':       { boxShadow: '0 0 16px rgba(0,212,255,0.8)' },
        },
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
    },
  },
  plugins: [],
}
