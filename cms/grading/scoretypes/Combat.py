#!/usr/bin/env python3

import json
from . import ScoreTypeAlone
from cms.db import SessionGen, Tahp
from cms.tahpRescoreRequest import makeRequest

import logging

logger = logging.getLogger(__name__)

# Dummy function to mark translatable string.
def N_(message):
    return message

def setTahp(task_name, data):
    with SessionGen() as session:
        tahp = session.query(Tahp).filter(Tahp.task == task_name).first()
        tahp.set_attrs({"data": json.dumps(data)})
        session.commit()

def getTahp(task_name):
    with SessionGen() as session:
        tahp = session.query(Tahp).filter(Tahp.task == task_name).first()
        session.commit()
        return json.loads(tahp.data)


class Combat(ScoreTypeAlone):
    """The score of a submission is the sum of the outcomes,
    multiplied by the integer parameter.

    """
    # Mark strings for localization.
    N_("#")
    N_("Outcome")
    N_("Details")
    N_("Execution time")
    N_("Memory used")
    N_("N/A")
    TEMPLATE = """\
<table class="testcase-list">
    <thead>
        <tr>
            <th class="idx">
                {% trans %}#{% endtrans %}
            </th>
            <th class="outcome">
                {% trans %}Outcome{% endtrans %}
            </th>
            <th class="details">
                {% trans %}Details{% endtrans %}
            </th>
    {% if feedback_level == FEEDBACK_LEVEL_FULL %}
            <th class="execution-time">
                {% trans %}Execution time{% endtrans %}
            </th>
            <th class="memory-used">
                {% trans %}Memory used{% endtrans %}
            </th>
    {% endif %}
        </tr>
    </thead>
    <tbody>
    {% for tc in details %}
        {% if "outcome" in tc and "text" in tc %}
            {% if tc["outcome"] == "Top server" %}
        <tr class="correct">
            {% elif tc["outcome"] == "Non" %}
        <tr class="notcorrect">
            {% else %}
        <tr class="partiallycorrect">
            {% endif %}
            <td class="idx">{{ loop.index }}</td>
            <td class="outcome">{{ _(tc["outcome"]) }}</td>
            <td class="details">{{ tc["text"]|format_status_text }}</td>
            {% if feedback_level == FEEDBACK_LEVEL_FULL %}
            <td class="execution-time">
                {% if tc["time"] is not none %}
                {{ tc["time"]|format_duration }}
                {% else %}
                {% trans %}N/A{% endtrans %}
                {% endif %}
            </td>
            <td class="memory-used">
                {% if tc["memory"] is not none %}
                {{ tc["memory"]|format_size }}
                {% else %}
                {% trans %}N/A{% endtrans %}
                {% endif %}
            </td>
            {% endif %}
        {% else %}
        <tr class="undefined">
            <td colspan="5">
                {% trans %}N/A{% endtrans %}
            </td>
        </tr>
        {% endif %}
    {% endfor %}
    </tbody>
</table>"""

    def __init__(self, parameters, public_testcases):
        params = json.loads(parameters)
        self.task_id = params['task_id']
        self.task_name = params['task_name']
        self.test_point = params['point']

        super().__init__(parameters, public_testcases)


    def max_scores(self):
        """See ScoreType.max_score."""
        public_score = 0.0
        score = 0.0
        for public in self.public_testcases.values():
            if public:
                public_score += self.test_point
            score += self.test_point
        return score, public_score, []

    def compute_score(self, submission_result):
        """See ScoreType.compute_score."""
        # Actually, this means it didn't even compile!
        if not submission_result.evaluated():
            return 0.0, [], 0.0, [], []

        # XXX Lexicographical order by codename
        indices = sorted(self.public_testcases.keys())
        evaluations = dict((ev.codename, ev)
                           for ev in submission_result.evaluations)
        testcases = []
        public_testcases = []
        score = 0.0
        public_score = 0.0

        tahp = getTahp(self.task_name)
        rescore = False
        for idx in indices:
            if idx not in tahp.keys():
                tahp[idx] = "10000000.0"
            
            if float(evaluations[idx].outcome) > 0 and float(evaluations[idx].outcome) < float(tahp[idx]):
                tahp[idx] = evaluations[idx].outcome
                rescore = True

            if float(evaluations[idx].outcome) < 1:
                this_score = 0
            else:
                this_score = (max(1.0, (float(tahp[idx]) - 1)) / max(1.0, float(evaluations[idx].outcome) - 1))**(1.7) * self.test_point
            
            if this_score < 0.001:
                this_score = 0

            tc_outcome = self.get_public_outcome(this_score)
            score += this_score
            testcases.append({
                "idx": idx,
                "outcome": tc_outcome,
                "text": evaluations[idx].text,
                "time": evaluations[idx].execution_time,
                "memory": evaluations[idx].execution_memory,
                })
            if self.public_testcases[idx]:
                public_score += this_score
                public_testcases.append(testcases[-1])
            else:
                public_testcases.append({"idx": idx})

        setTahp(self.task_name, tahp)
        if rescore:
            makeRequest(self.task_id)

        return score, testcases, public_score, public_testcases, []

    def get_public_outcome(self, outcome):
        """Return a public outcome from an outcome.

        outcome (float): the outcome of the submission.

        return (float): the public output.

        """
        if outcome <= 0.0:
            return N_("Non")
        elif outcome >= self.test_point:
            return N_("Top server")
        elif outcome >= self.test_point * 0.8:
            return N_("Mạnh vl")
        elif outcome >= self.test_point * 0.6:
            return N_("Cũng mạnh")
        elif outcome >= self.test_point * 0.4:
            return N_("Cần cố gắng")
        elif outcome >= self.test_point * 0.2:
            return N_("Tạm ổn")
        else:
            return N_("Hơi non")