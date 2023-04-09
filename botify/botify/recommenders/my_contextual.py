from .recommender import Recommender
import numpy as np

class MyContextual(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, recommendations_redis, fallback, tracks_redis_listened, catalog):
        self.tracks_redis = tracks_redis
        self.tracks_redis_listened = tracks_redis_listened
        self.fallback = fallback
        self.catalog = catalog
        self.recommendations_redis = recommendations_redis
        self.prev_recommender = 'tracks_redis'

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        listened = self.tracks_redis_listened.get(user)
        if listened is not None:
            listened = set(self.catalog.from_bytes(listened))
        else:
            listened = set()
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            self.prev_recommender = 'random'
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
        # if prev_track_time < 0.7 and self.prev_recommender == 'tracks_redis' or prev_track_time >= 0.7 and self.prev_recommender == 'recommendations_redis':
        #     self.prev_recommender = 'recommendations_redis'
        #     return self.recommendations_redis.recommend_next(user, prev_track, prev_track_time) 

        recommendations = list(previous_track.recommendations)
        weights = list(previous_track.weights)
        filtered_recommendations = []
        filtered_weights = []
        for weight, recommendation in zip(weights, recommendations):
            if recommendation not in listened:
                filtered_recommendations.append(recommendation)
                filtered_weights.append(weight)
        if len(recommendations) == 0:
            self.prev_recommender == 'random'
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
        self.prev_recommender == 'tracks_redis'
        next_track = filtered_recommendations[np.random.choice(np.arange(len(filtered_recommendations)), p=np.array(filtered_weights) / sum(filtered_weights))]
        listened.add(next_track)
        self.tracks_redis_listened.set(user, self.catalog.to_bytes(listened))
        return next_track
