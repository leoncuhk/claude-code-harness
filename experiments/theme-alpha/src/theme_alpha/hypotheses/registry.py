from . import h1_attention_leadlag, h2_concept_momentum_decay, h3_spillover, h4_crowding_filter

RUNNERS = {
    "H1": h1_attention_leadlag.run,
    "H2": h2_concept_momentum_decay.run,
    "H3": h3_spillover.run,
    "H4": h4_crowding_filter.run,
}
CONFIGS = {h: f"configs/hypotheses/{h.lower()}.yaml" for h in RUNNERS}
