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

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        
        history = self.tracks_redis_listened.get(user)
        if history is not None:
            history = self.catalog.from_bytes(history)
        else:
            history = {'listened': set(), 'last_recommender': None}
        listened = history['listened']
        prev_recommender = history['last_recommender']
        previous_track = self.tracks_redis.get(prev_track)

        if previous_track is None:
            track = self.fallback.recommend_next(user, prev_track, prev_track_time)
            listened.add(track)
            self.tracks_redis_listened.set(user, self.catalog.to_bytes({'listened': listened, 'last_recommender': 'random'}))
            return track

        if prev_track_time < 0.7 and prev_recommender == 'tracks_redis' or prev_track_time >= 0.7 and prev_recommender == 'recommendations_redis':
            track = self.recommendations_redis.recommend_next(user, prev_track, prev_track_time)
            listened.add(track)
            self.tracks_redis_listened.set(user, self.catalog.to_bytes({'listened': listened, 'last_recommender': 'recommendations_redis'}))
            return track

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = list(previous_track.recommendations)
        weights = list(previous_track.weights)
        filtered_recommendations = []
        filtered_weights = []
        for weight, recommendation in zip(weights, recommendations):
            if recommendation not in listened:
                filtered_recommendations.append(recommendation)
                filtered_weights.append(weight)
        if len(recommendations) == 0:
            track = self.fallback.recommend_next(user, prev_track, prev_track_time)
            listened.add(next_track)
            self.tracks_redis_listened.set(user, self.catalog.to_bytes({'listened': listened, 'last_recommender': 'random'}))
            return track
        next_track = filtered_recommendations[np.random.choice(np.arange(len(filtered_recommendations)), p=np.array(filtered_weights) / sum(filtered_weights))]
        listened.add(next_track)
        self.tracks_redis_listened.set(user, self.catalog.to_bytes({'listened': listened, 'last_recommender': 'tracks_redis'}))
        return next_track
