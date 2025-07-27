from langchain_core.runnables import Runnable
from collections import Counter


class CoTSCWrapper(Runnable):

    def __init__(self, llm, num_samples=5):

        self.llm = llm
        self.num_samples = num_samples

    def invoke(self, input, *args, **kwargs):
        responses = [self.llm.invoke(input) for _ in range(self.num_samples)]
        final_answers = [self.extract_answer(r) for r in responses]
        most_common = Counter(final_answers).most_common(1)[0][0]
        return most_common

    def extract_answer(self, text):

        return text.strip()
