from app.analysis_ai.graph.tools.human_task import human_task
from app.analysis_ai.graph.tools.log_improvement import log_improvement
from app.analysis_ai.graph.tools.hashlookup_api import check_hash_circl
from app.analysis_ai.graph.tools.finish_analysis import finish_analysis

AVAILABLE_TOOLS = [human_task, log_improvement, check_hash_circl, finish_analysis]
