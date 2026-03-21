from langchain_core.runnables import RunnableConfig
from app.analysis_ai.services.notifier import BaseNotifier


class GraphConfig:
    """
    Centralizes LangGraph configuration keys and dependency injection mapping.
    Ensures safe extraction and fail-fast validation to prevent mid-workflow crashes.
    """

    _CONFIG_NAMESPACE = "configurable"
    _NOTIFIER_KEY = "notifier"

    @classmethod
    def set_notifier(cls, notifier: BaseNotifier) -> RunnableConfig:
        """
        Builds the LangGraph-compliant config object and validates the contract
        prior to workflow execution. Fails immediately if invalid.
        """
        if not isinstance(notifier, BaseNotifier):
            raise TypeError(
                f"CRITICAL: Expected BaseNotifier instance, got {type(notifier).__name__}. "
                "Workflow execution aborted before LLM initialization."
            )

        return {cls._CONFIG_NAMESPACE: {cls._NOTIFIER_KEY: notifier}}

    @classmethod
    def get_notifier(cls, config: RunnableConfig) -> BaseNotifier:
        """
        Extracts the notifier from the graph context.
        """
        notifier = config.get(cls._CONFIG_NAMESPACE, {}).get(cls._NOTIFIER_KEY)

        if not isinstance(notifier, BaseNotifier):
            raise RuntimeError(
                "CRITICAL: BaseNotifier missing from execution context. "
                "State graph integrity compromised."
            )

        return notifier
