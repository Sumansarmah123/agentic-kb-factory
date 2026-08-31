"""
Agent Registry Service for Fortified Enterprise Fleet.
Central repository for publishing, versioning, and discovering enterprise-approved agents.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from backend.services.firestore import firestore_service

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Metadata for enterprise agent registry."""
    agent_id: str
    name: str
    version: str
    author: str
    description: str
    capabilities: List[str]
    approved: bool
    created_at: datetime
    updated_at: datetime
    department: Optional[str] = None
    compliance_tags: Optional[List[str]] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None


class AgentRegistryService:
    """
    Enterprise Agent Registry for discovery and governance.
    
    Track Requirement: "Agent Registry (the central repository for 
    publishing, versioning, and discovering enterprise-approved agents)."
    
    Features:
    - Agent registration and versioning
    - Discovery by department/capabilities
    - Approval workflow
    - Compliance tagging
    """
    
    COLLECTION = "agent_registry"
    
    async def register_agent(
        self,
        agent_id: str,
        name: str,
        version: str,
        author: str,
        description: str,
        capabilities: List[str],
        department: Optional[str] = None,
        compliance_tags: Optional[List[str]] = None,
        model: Optional[str] = None,
        tools: Optional[List[str]] = None,
    ) -> AgentMetadata:
        """
        Register a new agent in the enterprise catalog.
        
        Args:
            agent_id: Unique agent identifier
            name: Human-readable name
            version: Semantic version (e.g., "1.0.0")
            author: Agent creator
            description: Purpose and capabilities
            capabilities: List of what agent can do
            department: Optional department ownership
            compliance_tags: Optional compliance categories
            model: AI model used (e.g., "gemini-3.5-flash")
            tools: List of tools agent uses
            
        Returns:
            AgentMetadata with registration info
        """
        metadata = AgentMetadata(
            agent_id=agent_id,
            name=name,
            version=version,
            author=author,
            description=description,
            capabilities=capabilities,
            approved=False,  # Requires approval
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            department=department,
            compliance_tags=compliance_tags or [],
            model=model,
            tools=tools or [],
        )
        
        # Store in Firestore
        doc_id = f"{agent_id}_{version}"
        await firestore_service._get_collection(self.COLLECTION).document(doc_id).set(
            asdict(metadata)
        )
        
        logger.info(f"Registered agent: {agent_id} v{version}")
        return metadata
    
    async def discover_agents(
        self,
        department: Optional[str] = None,
        approved_only: bool = True,
        capability: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discover approved agents by department or capability.
        
        Args:
            department: Filter by department
            approved_only: Only return approved agents
            capability: Filter by specific capability
            
        Returns:
            List of agent metadata dicts
        """
        query = firestore_service._get_collection(self.COLLECTION)
        
        if approved_only:
            query = query.where("approved", "==", True)
        
        if department:
            query = query.where("department", "==", department)
        
        docs = query.stream()
        agents = []
        
        async for doc in docs:
            agent_data = doc.to_dict()
            
            # Filter by capability if specified
            if capability:
                if capability in agent_data.get("capabilities", []):
                    agents.append(agent_data)
            else:
                agents.append(agent_data)
        
        logger.info(f"Discovered {len(agents)} agents")
        return agents
    
    async def get_agent_version(
        self,
        agent_id: str,
        version: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific agent version.
        
        Args:
            agent_id: Agent identifier
            version: Version string
            
        Returns:
            Agent metadata dict or None
        """
        doc_id = f"{agent_id}_{version}"
        doc = await firestore_service._get_collection(self.COLLECTION).document(doc_id).get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    async def approve_agent(
        self,
        agent_id: str,
        version: str,
        approver: str,
    ) -> bool:
        """
        Approve agent for enterprise use.
        
        Args:
            agent_id: Agent identifier
            version: Version to approve
            approver: Person approving
            
        Returns:
            True if approved, False if not found
        """
        doc_id = f"{agent_id}_{version}"
        doc_ref = firestore_service._get_collection(self.COLLECTION).document(doc_id)
        
        doc = await doc_ref.get()
        if not doc.exists:
            logger.warning(f"Agent {doc_id} not found for approval")
            return False
        
        await doc_ref.update({
            "approved": True,
            "approved_by": approver,
            "approved_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        
        logger.info(f"Approved agent: {doc_id} by {approver}")
        return True
    
    async def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents (admin view)."""
        docs = firestore_service._get_collection(self.COLLECTION).stream()
        agents = []
        
        async for doc in docs:
            agents.append(doc.to_dict())
        
        return agents
    
    async def get_agent_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        docs = firestore_service._get_collection(self.COLLECTION).stream()
        
        total = 0
        approved = 0
        
        async for doc in docs:
            total += 1
            if doc.to_dict().get("approved"):
                approved += 1
        
        return {
            "total_agents": total,
            "approved_agents": approved,
            "pending_approval": total - approved,
        }


# Singleton instance
agent_registry_service = AgentRegistryService()


# Auto-register our agents on startup
async def register_builtin_agents():
    """Register Collector and Healer agents in the registry."""
    from backend.config import settings
    
    # Register Collector Agent
    await agent_registry_service.register_agent(
        agent_id="collector_agent",
        name="Knowledge Base Collector",
        version="1.0.0",
        author="Agentic KB Factory Team",
        description="Extracts structured data from web pages using CSS selectors",
        capabilities=["web_scraping", "data_extraction", "css_selector_matching"],
        department="Data Engineering",
        compliance_tags=["GDPR", "SOC2"],
        model=settings.collector_model,
        tools=["fetch_url", "extract_items"],
    )
    
    # Register Healer Agent
    await agent_registry_service.register_agent(
        agent_id="healer_agent",
        name="Self-Healing Selector Agent",
        version="1.0.0",
        author="Agentic KB Factory Team",
        description="Autonomously repairs broken CSS selectors using Gemini AI",
        capabilities=["dom_analysis", "selector_healing", "autonomous_repair"],
        department="Site Reliability Engineering",
        compliance_tags=["GDPR", "SOC2", "Autonomous AI"],
        model=settings.healer_model,
        tools=["fetch_current_html", "gemini_heal_selector"],
    )
    
    # Auto-approve both (they're built-in)
    await agent_registry_service.approve_agent("collector_agent", "1.0.0", "system")
    await agent_registry_service.approve_agent("healer_agent", "1.0.0", "system")
    
    logger.info("✅ Built-in agents registered and approved")
