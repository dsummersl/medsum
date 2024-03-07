from typing import Dict, List
from collections import Counter
from gensim import corpora, models
from gensim.utils import simple_preprocess
from nltk.corpus import stopwords
from collections import defaultdict
import nltk
import logging
from typing import Dict, List, TypedDict
import tomotopy as tp
from gensim.utils import simple_preprocess
from nltk.corpus import stopwords
from .vtt import time_string_to_seconds
import nltk


logger = logging.getLogger(__name__)

nltk.download("stopwords")


def assign_time_slices(data, num_slices):
    start_time = time_string_to_seconds(data[0]["start"])
    end_time = time_string_to_seconds(data[-1]["end"])
    total_duration = end_time - start_time
    slice_duration = total_duration / num_slices

    time_slices = []
    for datum in data:
        doc_time = time_string_to_seconds(datum["start"])
        time_slice = int((doc_time - start_time) / slice_duration)
        time_slices.append(
            min(time_slice, num_slices - 1)
        )  # Ensure the index is within bounds

    return time_slices


class Topic(TypedDict):
    words: str


class Transcript(TypedDict):
    id: str
    topic: int


class Topics(TypedDict):
    topics: Dict[int, Topic]
    transcripts: List[Transcript]


def identify_topics(data: List[Dict], max_topics: int = 5) -> Topics:
    # Preprocess the text data
    print("Finding topics...")
    stop_words = set(stopwords.words("english"))

    num_slices = 5
    time_slices = assign_time_slices(data, num_slices)

    # Create a DTModel
    dtm = tp.DTModel(
        tw=tp.TermWeight.IDF, t=num_slices, min_cf=0, rm_top=2, k=max_topics
    )

    # Add documents to the model
    doc_ids = []
    for i, datum in enumerate(data):
        text = [
            word for word in simple_preprocess(datum["text"]) if word not in stop_words
        ]
        idx = dtm.add_doc(text, time_slices[i])
        if idx is None:
            logger.debug("skipping document {0}".format(datum))
            continue
            # raise ValueError('Failed to add document to the model')
        doc_ids.append(
            {
                "id": datum["id"],
                "doc_id": idx,
            }
        )

    dtm.train(0)
    for i in range(100):
        dtm.train(10)

    topics = {}
    for did in doc_ids:
        doc = dtm.docs[did["doc_id"]]
        topic_dist = doc.get_topic_dist()
        if topic_dist.any():
            dominant_topic = topic_dist.argmax()
        else:
            dominant_topic = -1
        did["topic"] = dominant_topic
        topics[dominant_topic] = {"words": " ".join([w for w, _ in doc.get_words()])}

    return {
        "topics": topics,
        "transcripts": doc_ids,
    }


def identify_topics_gensim(data: List[Dict], max_topics: int = 5) -> Topics:
    stop_words = set(stopwords.words("english"))
    texts = [
        [word for word in simple_preprocess(segment["text"]) if word not in stop_words]
        for segment in data
    ]

    # Create a dictionary and corpus for LDA
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    hdp_model = models.HdpModel(corpus, id2word=dictionary, T=max_topics)

    topic_assignments = []
    for i in range(len(corpus)):
        topic_probs = hdp_model[corpus[i]]
        if topic_probs:  # Check if there are any topic assignments
            topic_assignments.append(
                {"id": data[i]["id"], "topic": max(topic_probs, key=lambda x: x[1])[0]}
            )
        else:
            topic_assignments.append({"id": data[i]["id"], "topic": -1})

    time_ranges = defaultdict(list)

    for i, segment in enumerate(data):
        topic = topic_assignments[i]["topic"]
        time_ranges[topic].append(segment["id"])

    consolidated_time_ranges = {}
    for topic, ranges in time_ranges.items():
        consolidated_time_ranges[topic] = ranges

    topics = {}
    for idx, topic in enumerate(
        hdp_model.show_topics(
            num_topics=len(consolidated_time_ranges.items()),
            num_words=10,
            formatted=False,
        )
    ):
        topics[idx] = {"words": " ".join([w for w, _ in topic[1]])}

    return {
        "topics": topics,
        "transcripts": [t for t in topic_assignments if t['topic'] >= 0],
    }


def split_by_dominant_topics(topics: List[int], threshold: float) -> List[List[int]]:
    # Count the occurrences of each topic
    counts = Counter(topics)
    total = len(topics)
    # Identify dominant topics
    dominant_topics = {topic for topic, count in counts.items() if count / total >= threshold}

    if len(dominant_topics) <= 1:
        if len(topics) > 0:
            return [[0, len(topics) - 1]]
        return []

    # Initialize the result array with the index ranges for groups of the dominant topics
    result = []

    # Track which dominant_topics have been addressed thus far
    finished_topics = set()

    counts_so_far = Counter({c: 0 for c in dominant_topics})
    dominant_threshold = 1 / len(dominant_topics)

    for i, topic in enumerate(topics):
        counts_so_far[topic] += 1

        # Check if any topic has become a majority
        for dt in dominant_topics - finished_topics:
            if counts_so_far[dt] / counts[dt] > dominant_threshold:
                finished_topics = finished_topics | {dt}
                dt_range = [0,i]
                if len(result) > 0:
                    dt_range[0] = result[-1][1] + 1
                result.append(dt_range)

    # Finalize the last range
    if len(result) > 0 and result[-1][1] != len(topics) - 1:
        result[-1][1] = len(topics) - 1

    return result
