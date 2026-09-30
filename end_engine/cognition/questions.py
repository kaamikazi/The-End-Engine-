from .state import QuestionInstance


class QuestionGenerator:
    def generate(self, operator, target, *, question_id, parent_step):
        return QuestionInstance(question_id, operator.name, target,
            f"Regarding {target.target_type.value.lower()} {target.target_id}: {target.text}\n"
            f"{operator.prompt_template}",
            f"A checkable finding about {target.dimension}: {operator.purpose.lower()}.",
            parent_step, operator.purpose)
