from abc import ABC, abstractmethod


class BaseLoader(ABC):
    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def load(self, index):
        pass

    @abstractmethod
    def find_index(self, record_id):
        pass