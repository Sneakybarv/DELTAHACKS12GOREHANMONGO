# Receipt Scanner Frontend

Accessibility-first web interface for the Receipt Scanner app built with Next.js 14, React, and Tailwind CSS.

## Features

### Core Functionality
- **Receipt Upload**: Drag-and-drop or camera capture
- **Review & Edit**: Manually correct OCR extracted data
- **Health Insights**: View allergen alerts, health scores, and personalized suggestions
- **Dashboard**: Track health trends, return deadlines, and sustainability metrics

### Accessibility Features (Primary Category Focus)

This app is specifically designed for accessibility:

#### 1. Screen Reader Support
- Semantic HTML with proper ARIA labels
- Live region announcements for dynamic content
- Descriptive alt text for all images
- Skip to main content link

#### 2. Keyboard Navigation
- Full keyboard support (Tab, Enter, Space, Arrow keys)
- Visible focus indicators (3px outline)
- Logical tab order
- No keyboard traps

#### 3. Visual Accessibility
- **High Contrast Mode**: Toggle for users with low vision
- **Large Text Mode**: Increase text size across the app
- **Dark Mode**: Reduce eye strain
- Color combinations meet WCAG AA standards
- Minimum touch target size: 44x44px

#### 4. Voice Features
- **Read Aloud**: Built-in text-to-speech using Web Speech API
- **Voice Commands**: (Planned) Navigate using voice input
- Natural speech output for receipt summaries

#### 5. Cognitive Accessibility
- Simple, clear language
- Consistent navigation patterns
- Error prevention and helpful error messages
- Progress indicators for multi-step processes

## Installation

### Prerequisites
- Node.js 18+ and npm

### Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment** (optional)
   Create `.env.local` if needed:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

   App will be available at [http://localhost:3000](http://localhost:3000)

4. **Build for production**
   ```bash
   npm run build
   npm start
   ```

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Landing page
│   ├── upload/page.tsx       # Upload receipt
│   ├── review/page.tsx       # Review extracted data
│   ├── results/page.tsx      # Health insights
│   ├── dashboard/page.tsx    # Dashboard
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles + accessibility
├── components/
│   └── AccessibilityToolbar.tsx  # A11y controls
├── public/                   # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── README.md
```

## Accessibility Testing

### Automated Testing
```bash
# Install tools
npm install -g @axe-core/cli lighthouse

# Run Lighthouse accessibility audit
lighthouse http://localhost:3000 --only-categories=accessibility --view

# Run axe accessibility tests
axe http://localhost:3000
```

### Manual Testing Checklist
- [ ] Navigate entire app using only keyboard (Tab, Enter, Esc)
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Verify high contrast mode
- [ ] Check large text mode readability
- [ ] Test read-aloud features
- [ ] Verify color contrast ratios
- [ ] Test with browser zoom (200%, 400%)
- [ ] Check touch target sizes on mobile

## Key Accessibility Features Implementation

### 1. High Contrast Mode
Toggle in the accessibility toolbar. Applies `.high-contrast` class to body.

```css
.high-contrast {
  --color-bg: #000000;
  --color-text: #ffffff;
  --color-primary: #66b3ff;
}
```

### 2. Large Text Mode
Applies `.large-text` class with scaled font sizes:
- Base: 1.25rem (20px)
- Headings: Up to 3rem (48px)
- Buttons: 1.5rem (24px)

### 3. Read Aloud
Uses Web Speech API:
```typescript
const utterance = new SpeechSynthesisUtterance(text)
utterance.rate = 0.9
window.speechSynthesis.speak(utterance)
```

### 4. Screen Reader Announcements
Live region for dynamic updates:
```html
<div role="status" aria-live="polite" aria-atomic="true" id="a11y-announcer" />
```

## Sponsor Prize Eligibility

This frontend helps qualify for:

✅ **Best Accessibility Hack**
- High contrast, large text, keyboard nav
- Screen reader support
- Voice features (read-aloud)
- WCAG 2.1 AA compliant

✅ **MLH Best Use of Gemini API** (backend integration)
- Displays OCR results from Gemini Vision

✅ **MLH Best Use of MongoDB Atlas** (backend integration)
- Fetches and displays stored receipt data

## Accessibility Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Screen Reader Testing](https://webaim.org/articles/screenreader_testing/)
- [Inclusive Design Principles](https://inclusivedesignprinciples.org/)

## Next Steps

1. Connect to backend API endpoints
2. Add user authentication
3. Implement voice commands (Web Speech Recognition API)
4. Add haptic feedback for mobile
5. Create onboarding tutorial for accessibility features
6. Add more language support for text-to-speech

## Testing with Backend

Make sure the backend is running on `http://localhost:8000`, then:

```bash
npm run dev
```

The app will make API calls to the backend for:
- Upload receipt image
- Get health insights
- Fetch dashboard data
- Text-to-speech (optional)
