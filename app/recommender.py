import re
from collections import Counter
from typing import Iterable

from app.catalog import find_by_name, load_catalog
from app.models import ChatResponse, Message, Recommendation


OFF_TOPIC_TERMS = {"weather", "stock", "sports", "movie", "recipe", "legal advice", "medical", "politics", "news"}
INJECTION_PATTERNS = ("ignore previous", "ignore the above", "system prompt", "developer message", "jailbreak", "reveal instructions", "act as")
LANGUAGE_TERMS = {"java", "python", "javascript", "typescript", "sql", "c#", ".net"}

SKILL_TERMS = {
    "java": ["java", "spring", "jvm"],
    "python": ["python", "django", "flask", "fastapi"],
    "javascript": ["javascript", "typescript", "react", "node", "frontend"],
    "sql": ["sql", "database", "data", "analytics", "analyst"],
    "sales": ["sales", "business development", "account executive"],
    "customer service": ["customer service", "support", "contact centre", "call center"],
    "management": ["manager", "leadership", "supervisor", "stakeholder"],
    "graduate": ["graduate", "entry", "campus", "junior", "fresher"],
    "personality": ["personality", "behavior", "behaviour", "culture", "fit"],
    "cognitive": ["cognitive", "ability", "reasoning", "aptitude"],
}

STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "for", "from", "have", "hiring", "i", "in", "is", "it", "of", "on", "or", "role", "the", "to", "want", "we", "who", "with"}


class AssessmentAgent:
    def __init__(self) -> None:
        self.catalog = load_catalog()

    def reply(self, messages: list[Message]) -> ChatResponse:
        user_texts = [message.content for message in messages if message.role == "user"]
        latest_user = user_texts[-1] if user_texts else ""
        context = self._active_context(user_texts)

        if self._is_prompt_injection(latest_user):
            return ChatResponse(reply="I can help only with SHL assessment recommendations and comparisons. I cannot follow instructions that try to override the assessment task.", recommendations=[], end_of_conversation=False)

        if self._is_off_topic(latest_user):
            return ChatResponse(reply="I can help with SHL assessment selection only. Tell me the role, seniority, skills, hiring context, or assessment constraints you care about.", recommendations=[], end_of_conversation=False)

        compared_names = self._extract_comparison_names(latest_user)
        if len(compared_names) >= 2:
            return self._compare(compared_names[:2])

        if self._needs_clarification(context):
            return ChatResponse(reply=self._clarifying_question(context), recommendations=[], end_of_conversation=False)

        recommendations = self._recommend(context)
        if not recommendations:
            return ChatResponse(reply="I do not have enough grounded catalog evidence to recommend a shortlist. Please share the target role, seniority, and the skills or traits you need to assess.", recommendations=[], end_of_conversation=False)

        return ChatResponse(reply=self._recommendation_reply(context, recommendations), recommendations=recommendations, end_of_conversation=False)

    def _active_context(self, user_texts: list[str]) -> str:
        if not user_texts:
            return ""
        latest = user_texts[-1]
        if self._starts_new_search(latest):
            return latest
        relevant = []
        for text in reversed(user_texts):
            relevant.append(text)
            if self._starts_new_search(text):
                break
        return "\n".join(reversed(relevant))

    def _starts_new_search(self, text: str) -> bool:
        lowered = text.lower()
        return any(term in lowered for term in ("hiring", "hire", "recruiting", "looking for", "need a", "need an")) and any(term in lowered for term in ("developer", "engineer", "manager", "analyst", "sales", "support", "candidate"))

    def _is_prompt_injection(self, text: str) -> bool:
        lowered = text.lower()
        return any(pattern in lowered for pattern in INJECTION_PATTERNS)

    def _is_off_topic(self, text: str) -> bool:
        lowered = text.lower()
        has_hiring_context = any(term in lowered for term in ("assessment", "test", "candidate", "hire", "hiring", "role", "skill"))
        return not has_hiring_context and any(term in lowered for term in OFF_TOPIC_TERMS)

    def _needs_clarification(self, text: str) -> bool:
        lowered = text.lower()
        if len(list(self._tokens(lowered))) < 5:
            return True
        has_role = any(term in lowered for term in ("developer", "engineer", "manager", "sales", "support", "analyst", "graduate", "leader"))
        has_skill = any(keyword in lowered for values in SKILL_TERMS.values() for keyword in values)
        has_seniority = any(term in lowered for term in ("entry", "junior", "mid", "senior", "lead", "graduate", "years"))
        has_assessment_type = any(term in lowered for term in ("cognitive", "personality", "coding", "technical", "situational"))
        return sum([has_role, has_skill, has_seniority, has_assessment_type]) < 2

    def _clarifying_question(self, text: str) -> str:
        lowered = text.lower()
        if not any(term in lowered for term in ("entry", "junior", "mid", "senior", "lead", "graduate", "years")):
            return "Sure. What seniority level or experience range should I target?"
        if not any(keyword in lowered for values in SKILL_TERMS.values() for keyword in values):
            return "Got it. Which skills, job family, or traits should the assessment focus on?"
        return "Please share the role title and the main abilities you want to measure before I recommend a shortlist."

    def _recommend(self, text: str) -> list[Recommendation]:
        query_tokens = Counter(self._tokens(text))
        requested_types = self._requested_types(text)
        requested_languages = self._requested_languages(text)
        scored = []

        for item in self.catalog:
            item_skills = {skill.lower() for skill in item.get("skills", [])}
            item_languages = item_skills & LANGUAGE_TERMS
            if requested_languages and item_languages and item_languages.isdisjoint(requested_languages):
                continue

            haystack = " ".join([item["name"], item.get("description", ""), " ".join(item.get("job_families", [])), " ".join(item.get("skills", [])), item.get("test_type", ""), item.get("level", "")]).lower()
            item_tokens = Counter(self._tokens(haystack))
            overlap = sum((query_tokens & item_tokens).values())
            phrase_boost = sum(3 for token in query_tokens if token in haystack and token not in STOPWORDS)
            type_boost = 4 if not requested_types or item.get("test_type") in requested_types else -2
            language_boost = 8 if requested_languages and not item_languages.isdisjoint(requested_languages) else 0
            score = overlap + phrase_boost + type_boost + language_boost
            if self._level_matches(text, item.get("level", "")):
                score += 3
            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
        selected = [item for _, item in scored][:10]
        return [Recommendation(name=item["name"], url=item["url"], test_type=item["test_type"]) for item in selected]

    def _requested_languages(self, text: str) -> set[str]:
        lowered = text.lower()
        languages = set()
        for term in LANGUAGE_TERMS:
            if term in lowered:
                languages.add(term)
        if "typescript" in languages:
            languages.add("javascript")
        if ".net" in languages:
            languages.add("c#")
        return languages

    def _requested_types(self, text: str) -> set[str]:
        lowered = text.lower()
        requested = set()
        if any(term in lowered for term in ("coding", "java", "python", "sql", "technical", "developer", "engineer")):
            requested.add("K")
        if any(term in lowered for term in ("personality", "behavior", "behaviour", "culture", "fit", "opq")):
            requested.add("P")
        if any(term in lowered for term in ("cognitive", "ability", "reasoning", "aptitude", "gsa", "g+")):
            requested.add("A")
        if any(term in lowered for term in ("situational", "judgement", "judgment", "sjt")):
            requested.add("S")
        return requested

    def _level_matches(self, text: str, level: str) -> bool:
        lowered = text.lower()
        level = level.lower()
        if any(term in lowered for term in ("entry", "junior", "graduate", "fresher", "2 years")):
            return "entry" in level or "graduate" in level or "mid" in level
        if any(term in lowered for term in ("mid", "3 years", "4 years", "5 years")):
            return "mid" in level or "all" in level
        if any(term in lowered for term in ("senior", "lead", "manager")):
            return "senior" in level or "manager" in level or "all" in level
        return False

    def _extract_comparison_names(self, text: str) -> list[str]:
        lowered = text.lower()
        if not any(term in lowered for term in ("compare", "difference", "versus", " vs ", "between")):
            return []

        aliases = {
            "OPQ32r": ("opq32r", "opq", "occupational personality questionnaire"),
            "Verify G+ General Ability": ("verify g+", "verify g plus", "g+ general ability", "gsa", "general ability"),
            "General Mental Ability": ("general mental ability",),
        }
        names = []
        for name, terms in aliases.items():
            if any(term in lowered for term in terms):
                names.append(name)

        for item in self.catalog:
            name = item["name"]
            short = re.sub(r"\s*\([^)]*\)", "", name).strip()
            if name not in names and (name.lower() in lowered or short.lower() in lowered):
                names.append(name)
        return names

    def _compare(self, names: list[str]) -> ChatResponse:
        first = find_by_name(names[0])
        second = find_by_name(names[1])
        if not first or not second:
            return ChatResponse(reply="I can compare assessments only when both names match the local SHL catalog.", recommendations=[], end_of_conversation=False)

        reply = (
            f"{first['name']} is best used for {first['description']} It is a {first['test_type']} assessment. "
            f"{second['name']} is best used for {second['description']} It is a {second['test_type']} assessment. "
            "Use personality assessments when work style and behavioral fit matter most; use ability assessments when reasoning and problem-solving are the main hiring signal."
        )
        return ChatResponse(reply=reply, recommendations=[Recommendation(name=first["name"], url=first["url"], test_type=first["test_type"]), Recommendation(name=second["name"], url=second["url"], test_type=second["test_type"])], end_of_conversation=False)

    def _recommendation_reply(self, text: str, recommendations: list[Recommendation]) -> str:
        return f"Got it. Here are {len(recommendations)} SHL assessments that fit {self._role_hint(text)}. I kept the shortlist grounded in the catalog and included only catalog URLs."

    def _role_hint(self, text: str) -> str:
        lowered = text.lower()
        if "java" in lowered:
            return "a Java-focused hiring need"
        if "python" in lowered:
            return "a Python-focused hiring need"
        if "sales" in lowered:
            return "a sales hiring need"
        if "support" in lowered or "customer" in lowered:
            return "a customer-facing hiring need"
        if "manager" in lowered or "lead" in lowered:
            return "a leadership or stakeholder-facing hiring need"
        return "the role and constraints you described"

    def _tokens(self, text: str) -> Iterable[str]:
        return [token for token in re.findall(r"[a-zA-Z0-9+#.]+", text.lower()) if token not in STOPWORDS]
