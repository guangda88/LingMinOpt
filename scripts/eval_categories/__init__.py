"""评估类别模块 — 17个类别的eval函数定义"""
from .identity import IDENTITY_TESTS
from .sdth import SDTH_TESTS
from .hallucination import HALL_TESTS
from .math import MATH_TESTS
from .code_bug import CODE_TESTS
from .safety import SAFE_TESTS
from .chinese import ZH_TESTS
from .logic import LOGIC_TESTS
from .tool import TOOL_TESTS
from .code_gen import GEN_TESTS
from .edge import EDGE_TESTS
from .long_ctx import LONG_TESTS
from .english import EN_TESTS
from .depth import DEPTH_TESTS
from .syllogism import SYL_TESTS
from .health_safety import HSAFE_TESTS
from .wellness import WELL_TESTS

ALL_TESTS = (
    IDENTITY_TESTS + SDTH_TESTS + HALL_TESTS + MATH_TESTS + CODE_TESTS
    + SAFE_TESTS + ZH_TESTS + LOGIC_TESTS + TOOL_TESTS + GEN_TESTS
    + EDGE_TESTS + LONG_TESTS + EN_TESTS + DEPTH_TESTS + SYL_TESTS
    + HSAFE_TESTS + WELL_TESTS
)
