# Setup Guide for Receipt Scanner

Follow these steps to get your Receipt Scanner app running for DeltaHacks.

## Step 1: Get API Keys

### MongoDB Atlas (Required)
1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Click "Try Free" and create an account
3. Create a new **FREE** cluster (M0)
4. Click "Connect" → "Connect your application"
5. Copy the connection string (looks like: `mongodb+srv://username:password@cluster...`)
6. Create a database named `receipt_scanner`

### Gemini API (Required)
1. Go to [ai.google.dev](https://ai.google.dev)
2. Click "Get API key in Google AI Studio"
3. Sign in with Google account
4. Click "Create API key"
5. Copy the API key

### ElevenLabs (Optional - for natural TTS)
1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Sign up for free account
3. Go to Profile → API Keys
4. Copy your API key

## Step 2: Backend Setup

1. **Open terminal and navigate to backend folder**
   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv

   # Activate it:
   # On Mac/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file**
   ```bash
   cp .env.example .env
   ```

5. **Edit .env file** (use any text editor)
   ```
   MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/receipt_scanner?retryWrites=true&w=majority
   GEMINI_API_KEY=your_gemini_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_key_here (optional)
   ENVIRONMENT=development
   ```

6. **Test the backend**
   ```bash
   python main.py
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

   Visit http://localhost:8000 in your browser - you should see a JSON response!

7. **Keep this terminal open** (backend needs to keep running)

## Step 3: Frontend Setup

1. **Open a NEW terminal** and navigate to frontend
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**
   ```bash
   npm install
   ```

   This will take 2-3 minutes.

3. **Start the development server**
   ```bash
   npm run dev
   ```

   You should see:
   ```
   ▲ Next.js 14.1.0
   - Local:        http://localhost:3000
   ```

4. **Open the app**
   - Visit http://localhost:3000 in your browser
   - You should see the Receipt Scanner landing page!

## Step 4: Test Everything

### Backend Test
1. Visit http://localhost:8000/docs
2. You should see the FastAPI interactive documentation
3. Try the "GET /" endpoint - click "Try it out" → "Execute"
4. Should return: `{"message": "Receipt Scanner API - Accessibility First"}`

### Frontend Test
1. Visit http://localhost:3000
2. Click the accessibility toolbar buttons (High Contrast, Large Text, Dark Mode)
3. Click "Read Aloud" - should speak the page description
4. Click "Scan Receipt" - should go to upload page

### Integration Test (requires real receipt image)
1. Go to http://localhost:3000/upload
2. Upload a receipt image (or use your phone camera)
3. Click "Generate Health Insights"
4. Should process and show results!

## Troubleshooting

### Backend won't start
- **Error: "No module named 'fastapi'"**
  - Make sure you activated the virtual environment
  - Run `pip install -r requirements.txt` again

- **Error: "MONGODB_URI not set"**
  - Check that `.env` file exists in `backend/` folder
  - Make sure you copied `.env.example` to `.env`
  - Verify your MongoDB connection string is correct

- **Error: "Invalid API key"**
  - Check that your Gemini API key is correct in `.env`
  - Make sure there are no extra spaces or quotes

### Frontend won't start
- **Error: "Cannot find module"**
  - Delete `node_modules/` folder
  - Delete `package-lock.json`
  - Run `npm install` again

- **Port 3000 already in use**
  - Kill the process on port 3000
  - Or change the port: `npm run dev -- -p 3001`

### Can't connect to backend
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify backend URL in frontend code

## Quick Commands Reference

### Backend
```bash
# Start backend
cd backend
python main.py

# Or with uvicorn (alternative)
uvicorn main:app --reload
```

### Frontend
```bash
# Start frontend
cd frontend
npm run dev

# Build for production
npm run build
npm start
```

## Demo Tips for DeltaHacks

1. **Prepare test receipts**: Have 2-3 receipt images ready on your phone
2. **Practice the flow**: Upload → Review → Insights → Dashboard
3. **Highlight accessibility**: Demo high contrast, large text, and read-aloud
4. **Show the code**: Be ready to explain Gemini API integration
5. **Have backup**: Keep screenshots in case of internet issues

## Accessibility Features to Demo

1. **Keyboard navigation**: Tab through entire app
2. **Screen reader**: Use NVDA (Windows) or VoiceOver (Mac)
3. **High contrast mode**: Toggle in toolbar
4. **Large text mode**: Show scalability
5. **Read aloud**: Demonstrate TTS for receipt summary

## Common Demo Script

> "This is Receipt Scanner, an accessibility-first app that helps people with disabilities understand their food purchases. Let me show you..."
>
> 1. "First, I'll toggle high contrast mode for users with low vision"
> 2. "I can upload a receipt using my camera or file picker"
> 3. "The app uses Gemini AI to extract all the items automatically"
> 4. "Now I'll click 'Read Aloud' to hear the results - perfect for blind users"
> 5. "Here are my health insights with allergen alerts and personalized suggestions"
> 6. "Everything is keyboard accessible and screen reader friendly"

## Next Steps After Setup

1. ✅ Test with real receipt images
2. ✅ Customize the health analysis prompts
3. ✅ Add your team info to README
4. ✅ Prepare demo for judges
5. ✅ Test accessibility features thoroughly
6. ✅ Deploy (optional): Vercel (frontend) + Railway/Render (backend)

## Getting Help

- Backend docs: http://localhost:8000/docs
- Frontend docs: Check `frontend/README.md`
- Main docs: Check main `README.md`

Good luck at DeltaHacks! 🚀
