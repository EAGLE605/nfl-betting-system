# 🧪 Backtesting & Training Lab

## Overview

The **Backtesting & Training Lab** is a visual, real-time interface for AI model training and strategy backtesting. Inspired by Lego building experiences, it makes complex machine learning processes simple, beautiful, and satisfying to watch.

## Features

### 🎯 Visual Pipeline
- **5-Stage Build Process**: Watch strategies move through generation, testing, validation, analysis, and deployment
- **Lego Block Visualization**: Each strategy appears as a colorful block that "snaps into place"
- **Real-Time Progress**: Live progress bars show exactly what's happening at each stage
- **Status Indicators**: Clear badges show whether stages are pending, running, or complete

### 📊 Live Statistics
- **Cycle Counter**: Track how many training cycles have run
- **Strategy Metrics**: See generated, tested, validated, and deployed counts
- **Performance Dashboard**: Real-time win rate, ROI, Sharpe ratio, and max drawdown
- **Historical Charts**: Track performance evolution over multiple cycles

### 🎮 Interactive Controls
- **Start/Pause Training**: Control continuous training loops
- **Single Cycle**: Run one cycle at a time for careful observation
- **View History**: Explore past training results
- **Reset Lab**: Start fresh when needed

### 📈 Results Analytics
- **Performance Over Time**: Charts showing win rate and ROI evolution
- **Strategy Tracking**: See how many strategies pass validation
- **Metrics Evolution**: Watch key indicators improve across cycles
- **Validation Rates**: Monitor how selective the system is

## How It Works

### The 5-Stage Pipeline

```
1. 🧠 Generate Strategies (Target: 10)
   └─> AI creates new betting strategies using various approaches

2. ⏮️ Run Backtests (Target: 5)
   └─> Test top strategies on historical game data

3. ✅ Validate Results (Target: 5)
   └─> 5-agent swarm votes on which strategies are production-ready

4. 📊 Analyze & Learn (Target: 1)
   └─> Extract insights and patterns from successful strategies

5. 🚀 Deploy Winners (Target: 3)
   └─> Best strategies go live for real betting
```

### Visual Design Philosophy

**Like Building with Lego:**
- Each strategy is a colorful block
- Blocks "float" and animate when being processed
- Completed stages show assembled structures
- Active stages pulse with energy
- Colors indicate stage type (purple = strategy, green = validation, gold = deployed)

**Non-Technical Language:**
- "Generate" not "Train Model"
- "Test on Historical Games" not "Run Backtest"
- "5-Agent Swarm Votes" not "Validation Pipeline"
- Visual metaphors over technical jargon

### Integration

The Lab integrates with:
- `src/backtesting/ai_orchestrator.py` - AI training cycles
- `src/backtesting/engine.py` - Walk-forward backtesting
- `src/swarms/strategy_generation_swarm.py` - Strategy generation
- `src/swarms/validation_swarm.py` - Strategy validation

## Usage

### Access the Lab

1. Open the dashboard: `streamlit run dashboard/app.py`
2. Navigate to the "🧪 Backtest" tab
3. Select "🧪 Training Lab" view mode
4. Click "▶️ Start Training" to begin

### View Modes

**🧪 Training Lab** (New!)
- Visual, real-time training interface
- Perfect for watching the system learn
- Great for demos and understanding

**📊 Results** (Legacy)
- Traditional backtest results view
- Shows historical performance metrics
- Includes equity curves and bet history

### Running a Single Cycle

Click "🔄 Run Single Cycle" to:
1. Generate 10 new strategies
2. Test top 5 on historical data
3. Validate results with 5-agent swarm
4. Analyze performance
5. Deploy winners (typically 1-3 strategies)

**Duration**: 30-60 seconds per cycle (depending on data size)

### Continuous Training

Click "▶️ Start Training" to run cycles automatically:
- System generates and tests strategies continuously
- Best performers are deployed automatically
- Performance metrics update in real-time
- Click "⏸️ Pause Training" to stop

## Architecture

### State Management

```python
st.session_state.lab_state = {
    'is_running': False,              # Training active?
    'current_stage': 'idle',          # Current pipeline stage
    'cycle_number': 0,                # Total cycles run
    'strategies_generated': 0,        # Total strategies created
    'strategies_tested': 0,           # Total strategies tested
    'strategies_validated': 0,        # Total passed validation
    'strategies_deployed': 0,         # Total deployed
    'current_metrics': {},            # Latest performance
    'history': [],                    # All cycle results
    'stage_progress': {}              # Progress per stage
}
```

### CSS Classes

**Stage Cards:**
- `.stage-container.active` - Currently running stage (pulses green)
- `.stage-container.complete` - Finished stage (green gradient)
- `.stage-container.pending` - Not yet started (faded)

**Lego Blocks:**
- `.lego-block` - Base block style (blue gradient, floating animation)
- `.lego-block.strategy` - Purple blocks for strategies
- `.lego-block.validation` - Green blocks for validated strategies
- `.lego-block.deployed` - Gold blocks for deployed strategies

**Status Badges:**
- `.status-badge.running` - Blue badge with "⚡ Running"
- `.status-badge.complete` - Green badge with "✓ Complete"
- `.status-badge.error` - Red badge with error state

## Performance

### Optimization Techniques

1. **Incremental Rendering**: Only update changed components
2. **Lazy Loading**: Import modules on-demand
3. **State Caching**: Persist state in session
4. **Efficient Charts**: Use Plotly for fast rendering

### Resource Usage

- **Memory**: ~50MB for lab interface
- **CPU**: Minimal (mostly waiting on AI processes)
- **Network**: None (all local processing)

## Customization

### Changing Animation Speed

Edit `dashboard/backtesting_lab.py`:

```python
# Lego block float animation (default: 3s)
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

# Change to 1.5s for faster animation
animation: float 1.5s ease-in-out infinite;
```

### Adjusting Color Scheme

```python
# Strategy blocks (default: purple)
.lego-block.strategy {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

# Change to blue
.lego-block.strategy {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}
```

### Adding New Stages

1. Add stage to `stages` list in `_render_build_pipeline()`
2. Update `stage_progress` dict in state
3. Add progress logic in `_simulate_cycle()`

## Troubleshooting

### Lab Won't Load

**Error**: "Error loading Backtesting Lab"

**Solution**:
1. Check `dashboard/backtesting_lab.py` exists
2. Verify Python path is correct
3. Switch to "📊 Results" view as fallback

### Training Cycle Fails

**Error**: Cycle completes but shows poor metrics

**Solution**:
1. Check if models exist in `models/` directory
2. Verify feature data in `data/processed/`
3. Ensure historical data covers test period

### Charts Not Updating

**Issue**: Metrics don't change after cycle

**Solution**:
1. Click "🔄 Refresh Results"
2. Check browser console for errors
3. Restart Streamlit server

## Examples

### Demo Mode (Current)

The lab currently runs in **simulation mode** for demonstration:
- Generates mock cycle results
- Shows realistic metrics
- Demonstrates visual interface
- No actual AI training yet

### Production Mode (Future)

To connect real AI training:

```python
# Replace _simulate_cycle() with real integration
async def _run_real_cycle(self) -> Dict:
    """Run actual AI backtesting cycle."""
    from src.backtesting.ai_orchestrator import AIBacktestOrchestrator
    
    orchestrator = AIBacktestOrchestrator(
        strategy_agents=[...],
        validation_agents=[...]
    )
    
    result = await orchestrator.run_cycle()
    return result
```

## Future Enhancements

### Planned Features
- [ ] Real-time WebSocket updates (no page refresh needed)
- [ ] Sound effects for completed stages
- [ ] Drag-and-drop strategy customization
- [ ] 3D visualization of strategy performance
- [ ] Export training reports to PDF
- [ ] Share training results via link
- [ ] Mobile-optimized touch controls
- [ ] Dark mode support

### Integration Roadmap
1. **Week 1**: Connect to real AI orchestrator
2. **Week 2**: Add real-time performance tracking
3. **Week 3**: Implement strategy customization UI
4. **Week 4**: Add advanced analytics dashboard

## Philosophy

### Design Principles

1. **Visual First**: Show, don't tell
2. **Simple Language**: No jargon or technical terms
3. **Immediate Feedback**: Every action has visible result
4. **Progressive Disclosure**: Start simple, reveal complexity gradually
5. **Delightful Interactions**: Make it fun to watch

### Inspired By

- **Lego Digital Designer**: Building block metaphor
- **Apple Watch Activity Rings**: Progress visualization
- **Stripe Dashboard**: Clean metrics display
- **Linear App**: Smooth animations and micro-interactions

## Credits

**Built with:**
- Streamlit (UI framework)
- Plotly (Charts and graphs)
- Custom CSS (Animations and styling)

**Design inspiration:**
- Modern design systems (Tailwind, Figma)
- Game UI (satisfying feedback loops)
- Data visualization best practices

---

**Questions or suggestions?** Open an issue on GitHub!

**Want to contribute?** PRs welcome for new animations, charts, or features!

