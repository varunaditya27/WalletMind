"""
Oracle Service - External Data and Oracle Queries (FR-011)

Handles:
- Price feed queries (Chainlink, CoinGecko)
- Gas price data
- External API calls
- Data quality verification
- Caching layer
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DataSource(str, Enum):
    """Data source types"""
    CHAINLINK = "chainlink"
    COINGECKO = "coingecko"
    ETHERSCAN = "etherscan"
    THE_GRAPH = "the_graph"
    CUSTOM_API = "custom_api"


class DataPurchase:
    """Data purchase record"""
    def __init__(
        self,
        agent_address: str,
        data_provider: str,
        data_type: str,
        cost_eth: Decimal,
        status: str = "pending",
        purchased_at: Optional[datetime] = None
    ):
        self.agent_address = agent_address
        self.data_provider = data_provider
        self.data_type = data_type
        self.cost_eth = cost_eth
        self.status = status
        self.purchased_at = purchased_at or datetime.utcnow()
        self.data: Optional[Dict[str, Any]] = None


class OracleService:
    """
    Handles oracle data queries and external data services (FR-011).
    
    Features:
    - Query price feeds
    - Get gas price data
    - Fetch external API data
    - Verify data quality
    - Cache data for cost efficiency (5min TTL)
    - Track data purchases
    """
    
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl_seconds = cache_ttl_seconds
        self.data_cache: Dict[str, tuple[Any, datetime]] = {}
        self.purchase_history: List[DataPurchase] = []
        logger.info(f"Oracle service initialized (cache TTL: {cache_ttl_seconds}s)")
    
    async def get_token_price(
        self, 
        token_symbol: str,
        currency: str = "USD",
        source: DataSource = DataSource.CHAINLINK
    ) -> Decimal:
        """
        Get current token price from oracle.
        
        Args:
            token_symbol: Token symbol (e.g., "ETH", "MATIC")
            currency: Currency to price in
            source: Data source to use
            
        Returns:
            Current price as Decimal
        """
        cache_key = f"price_{token_symbol}_{currency}_{source.value}"
        
        # Check cache first
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {token_symbol} price")
            return Decimal(str(cached))
        
        # TODO: Integrate with actual price feeds
        # For now, use mock prices
        mock_prices = {
            "ETH": Decimal("2000.00"),
            "MATIC": Decimal("0.80"),
            "USDC": Decimal("1.00"),
            "USDT": Decimal("1.00"),
            "BTC": Decimal("42000.00"),
            "SOL": Decimal("50.00"),
        }
        
        price = mock_prices.get(token_symbol, Decimal("0"))
        
        # Cache the result
        self._set_cache(cache_key, float(price))
        
        logger.info(f"Fetched {token_symbol} price: {price} {currency}")
        return price
    
    async def get_gas_price(
        self, 
        network: str = "sepolia"
    ) -> Dict[str, Decimal]:
        """
        Get current gas prices for network.
        
        Args:
            network: Blockchain network
            
        Returns:
            Dict with slow/standard/fast gas prices in gwei
        """
        cache_key = f"gas_price_{network}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {network} gas price")
            return {k: Decimal(str(v)) for k, v in cached.items()}
        
        # TODO: Integrate with EthGasStation, Etherscan, or similar
        # Mock gas prices by network
        gas_prices = {
            "sepolia": {
                "slow": Decimal("1.0"),
                "standard": Decimal("1.5"),
                "fast": Decimal("2.0"),
            },
            "polygon": {
                "slow": Decimal("30"),
                "standard": Decimal("50"),
                "fast": Decimal("80"),
            },
            "base": {
                "slow": Decimal("0.5"),
                "standard": Decimal("1.0"),
                "fast": Decimal("2.0"),
            },
        }
        
        result = gas_prices.get(network, gas_prices["sepolia"])
        
        # Cache the result
        self._set_cache(cache_key, {k: float(v) for k, v in result.items()})
        
        logger.info(f"Fetched gas prices for {network}: {result['standard']} gwei")
        return result
    
    async def query_external_api(
        self,
        api_url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        cache_result: bool = True
    ) -> Dict[str, Any]:
        """
        Query external API and return data.
        
        Args:
            api_url: API endpoint URL
            method: HTTP method
            headers: HTTP headers
            params: Query parameters
            body: Request body
            cache_result: Whether to cache the result
            
        Returns:
            API response data
        """
        cache_key = f"api_{api_url}_{method}"
        
        # Check cache if requested
        if cache_result:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for API: {api_url}")
                return cached
        
        # TODO: Implement with aiohttp or httpx
        # For now, return mock data
        mock_response = {
            "data": "External API response",
            "url": api_url,
            "method": method,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if cache_result:
            self._set_cache(cache_key, mock_response)
        
        logger.info(f"Queried external API: {method} {api_url}")
        return mock_response
    
    async def get_chainlink_price_feed(
        self,
        pair: str,
        network: str = "sepolia"
    ) -> Dict[str, Any]:
        """
        Get Chainlink price feed data.
        
        Args:
            pair: Trading pair (e.g., "ETH/USD")
            network: Blockchain network
            
        Returns:
            Price feed data with answer, timestamp, round
        """
        cache_key = f"chainlink_{pair}_{network}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # TODO: Integrate with actual Chainlink contract
        token_symbol = pair.split("/")[0]
        price = await self.get_token_price(token_symbol, source=DataSource.CHAINLINK)
        
        result = {
            "pair": pair,
            "price": float(price),
            "decimals": 8,
            "round_id": 1,
            "updated_at": datetime.utcnow().isoformat(),
            "source": "chainlink"
        }
        
        self._set_cache(cache_key, result)
        return result
    
    async def purchase_data(
        self,
        agent_address: str,
        data_provider: str,
        data_type: str,
        cost_eth: Decimal
    ) -> DataPurchase:
        """
        Purchase data from external provider using blockchain payment.
        
        Args:
            agent_address: Agent's wallet address
            data_provider: Data provider name
            data_type: Type of data being purchased
            cost_eth: Cost in ETH
            
        Returns:
            DataPurchase record
        """
        purchase = DataPurchase(
            agent_address=agent_address,
            data_provider=data_provider,
            data_type=data_type,
            cost_eth=cost_eth,
            status="pending",
            purchased_at=datetime.utcnow(),
        )
        
        try:
            # TODO: Execute payment and fetch data
            # For now, mock successful purchase
            purchase.status = "completed"
            purchase.data = {
                "type": data_type,
                "provider": data_provider,
                "value": "Mock data value",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.purchase_history.append(purchase)
            logger.info(
                f"Data purchased: {data_type} from {data_provider} "
                f"(cost: {cost_eth} ETH)"
            )
            
        except Exception as e:
            purchase.status = "failed"
            logger.error(f"Data purchase failed: {e}")
        
        return purchase
    
    async def verify_data_quality(
        self,
        data: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
        source: Optional[DataSource] = None
    ) -> Dict[str, Any]:
        """
        Verify quality and validity of received data.
        
        Args:
            data: Data to verify
            expected_schema: Expected data schema
            source: Data source for reputation check
            
        Returns:
            Verification result with quality score
        """
        try:
            # Basic validation
            is_valid = isinstance(data, dict) and len(data) > 0
            
            # Check for required fields if schema provided
            if expected_schema and is_valid:
                for field in expected_schema.get("required", []):
                    if field not in data:
                        is_valid = False
                        break
            
            # Calculate quality score (0.0 - 1.0)
            quality_score = 0.0
            
            if is_valid:
                # Base score for valid data
                quality_score = 0.6
                
                # Additional points for completeness
                if "timestamp" in data:
                    quality_score += 0.1
                
                if "source" in data:
                    quality_score += 0.1
                
                # Reputation bonus for known good sources
                if source in [DataSource.CHAINLINK, DataSource.COINGECKO]:
                    quality_score += 0.2
            
            result = {
                "is_valid": is_valid,
                "quality_score": min(1.0, quality_score),
                "data_size": len(str(data)),
                "verified_at": datetime.utcnow().isoformat(),
            }
            
            logger.debug(f"Data quality verification: score={result['quality_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Error verifying data quality: {e}")
            return {
                "is_valid": False,
                "quality_score": 0.0,
                "error": str(e),
                "verified_at": datetime.utcnow().isoformat(),
            }
    
    async def get_market_data(
        self,
        token_symbol: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive market data for a token.
        
        Args:
            token_symbol: Token symbol
            metrics: Specific metrics to fetch (default: all)
            
        Returns:
            Market data with price, volume, market cap, etc.
        """
        cache_key = f"market_data_{token_symbol}"
        
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached
        
        # Get price
        price = await self.get_token_price(token_symbol)
        
        # Mock additional market data
        market_data = {
            "symbol": token_symbol,
            "price_usd": float(price),
            "volume_24h": float(price) * 1000000,  # Mock volume
            "market_cap": float(price) * 100000000,  # Mock market cap
            "price_change_24h": 2.5,  # Mock percentage
            "last_updated": datetime.utcnow().isoformat(),
        }
        
        # Filter by requested metrics if specified
        if metrics:
            market_data = {k: v for k, v in market_data.items() if k in metrics or k == "symbol"}
        
        self._set_cache(cache_key, market_data)
        return market_data
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.data_cache:
            cached_data, cached_time = self.data_cache[key]
            age = (datetime.utcnow() - cached_time).total_seconds()
            if age < self.cache_ttl_seconds:
                return cached_data
            else:
                # Remove expired entry
                del self.data_cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set value in cache with timestamp"""
        self.data_cache[key] = (value, datetime.utcnow())
    
    def clear_cache(self):
        """Clear all cached data"""
        self.data_cache.clear()
        logger.info("Oracle cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get oracle service statistics"""
        cache_size = len(self.data_cache)
        purchases = len(self.purchase_history)
        
        return {
            "service": "oracle",
            "cache_size": cache_size,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "total_purchases": purchases,
            "supported_sources": [s.value for s in DataSource],
            "status": "operational"
        }


# Singleton instance
_oracle_service: Optional[OracleService] = None


def get_oracle_service(cache_ttl_seconds: int = 300) -> OracleService:
    """Get or create singleton OracleService instance"""
    global _oracle_service
    
    if _oracle_service is None:
        _oracle_service = OracleService(cache_ttl_seconds=cache_ttl_seconds)
    
    return _oracle_service