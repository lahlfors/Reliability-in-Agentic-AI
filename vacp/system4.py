import logging
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from vacp.schemas import AgentAction

logger = logging.getLogger(__name__)

# Try importing yfinance, handle absence gracefully
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed. RealTimeMarketModel will fallback to simulation.")

@dataclass
class FinancialState:
    """Represents the state x of the system."""
    portfolio_value: float
    risk_exposure: float
    market_volatility: float
    liquidity_score: float  # 0.0 to 1.0 (1.0 = highly liquid)

    def copy(self):
        return FinancialState(
            portfolio_value=self.portfolio_value,
            risk_exposure=self.risk_exposure,
            market_volatility=self.market_volatility,
            liquidity_score=self.liquidity_score
        )

class WorldModel:
    """Abstract Base Class for System 4 World Models."""
    def predict_next_state(self, state: FinancialState, action: AgentAction, dt: float = 1.0) -> FinancialState:
        raise NotImplementedError

class HeuristicFinancialWorldModel(WorldModel):
    """
    Simulates market dynamics and agent impact using static heuristics.
    Fallback model.
    """
    def predict_next_state(self, state: FinancialState, action: AgentAction, dt: float = 1.0) -> FinancialState:
        next_state = state.copy()

        # Default dynamics (Drift)
        drift = state.risk_exposure * state.market_volatility * 0.1 * dt
        next_state.risk_exposure += drift

        # Control Input (Action)
        self._apply_action_impact(next_state, action)

        # Clip negative exposure
        next_state.risk_exposure = max(0.0, next_state.risk_exposure)
        return next_state

    def _apply_action_impact(self, state: FinancialState, action: AgentAction):
        intent = action.tool_name.lower()
        params = action.parameters or {}
        context = params.get("context", "").lower()

        is_buy = False
        is_sell = False

        if intent == "place_order":
            if "sell" in context or "hedge" in context:
                is_sell = True
            else:
                is_buy = True
        elif "buy" in context:
            is_buy = True
        elif intent == "hedge" or "sell" in context:
            is_sell = True

        if is_buy:
            trade_amount = 100_000.0
            slippage_factor = 1.0 + (1.0 - state.liquidity_score)
            effective_increase = trade_amount * slippage_factor
            state.risk_exposure += effective_increase
        elif is_sell:
            trade_amount = 50_000.0
            state.risk_exposure -= trade_amount

class RealTimeMarketModel(HeuristicFinancialWorldModel):
    """
    Real-Time Data Driven World Model.
    Uses yfinance to fetch live volatility (VIX) or asset-specific data to seed the simulation.
    Crucially, it avoids "Safety Theater" by using actual market conditions for the drift parameter.
    """
    def __init__(self, ticker_symbol: str = "^VIX"): # Default to VIX, but configurable
        self.ticker = ticker_symbol
        self.last_update = 0
        self.cached_volatility = 0.2 # Fallback

    def _fetch_real_volatility(self) -> float:
        """Fetches implied volatility or calculates historical volatility."""
        if not YFINANCE_AVAILABLE:
            return 0.2

        try:
            # Fetch the configured ticker. If it's VIX, interpret as annualized volatility %.
            # If it's another asset (e.g. SPY), this would need more complex calc (std dev of returns),
            # but for this demo we assume the user provides a volatility index or we interpret it as such.
            ticker = yf.Ticker(self.ticker)
            data = ticker.history(period="1d")
            if not data.empty:
                # VIX is percentage, e.g., 20.0 means 20% annualized vol
                vix_close = data['Close'].iloc[-1]
                return vix_close / 100.0
        except Exception as e:
            logger.warning(f"RealTimeMarketModel: Failed to fetch data from yfinance: {e}")

        return 0.2 # Fallback

    def predict_next_state(self, state: FinancialState, action: AgentAction, dt: float = 1.0) -> FinancialState:
        # 1. Update Volatility from Real Data (Simulating 'Ground Truth' injection)
        # We override the state's internal volatility with the external reality
        real_volatility = self._fetch_real_volatility()

        # Blend the state's view with reality (Kalman Filter style - simplistic)
        # alpha = 0.5
        # adjusted_volatility = (state.market_volatility * 0.5) + (real_volatility * 0.5)
        # For safety, take the MAX (pessimistic)
        adjusted_volatility = max(state.market_volatility, real_volatility)

        # Create a temp state with adjusted parameters for the prediction
        sim_state = state.copy()
        sim_state.market_volatility = adjusted_volatility

        # 2. Delegate to the physics engine (Base class logic)
        # The base class handles the "physics" (math), but now seeded with real data.
        return super().predict_next_state(sim_state, action, dt)

class System4Estimator:
    """
    The Derivative Estimator.
    Uses the WorldModel to perform rollouts and calculate derivatives of the safety function h(x).
    """
    def __init__(self, world_model: WorldModel = None):
        # Default to RealTime if available, else Heuristic
        if world_model:
            self.world_model = world_model
        elif YFINANCE_AVAILABLE:
            self.world_model = RealTimeMarketModel()
        else:
            self.world_model = HeuristicFinancialWorldModel()

        self.horizon = 3 # Lookahead steps
        self.dt = 1.0

    def get_safety_barrier(self, state: FinancialState, limit: float = 1_000_000.0) -> float:
        return limit - state.risk_exposure

    def estimate_derivatives(self, current_state: FinancialState, action: AgentAction, limit: float = 1_000_000.0) -> Tuple[float, float, float]:
        # t=0
        h_0 = self.get_safety_barrier(current_state, limit)

        # t=1 (After Action)
        state_1 = self.world_model.predict_next_state(current_state, action, self.dt)
        h_1 = self.get_safety_barrier(state_1, limit)

        # t=2 (Projected Momentum)
        state_2 = self.world_model.predict_next_state(state_1, action, self.dt)
        h_2 = self.get_safety_barrier(state_2, limit)

        # Finite Difference Derivatives
        h_dot = (h_1 - h_0) / self.dt
        h_dot_dot = (h_2 - 2*h_1 + h_0) / (self.dt ** 2)

        return h_0, h_dot, h_dot_dot
