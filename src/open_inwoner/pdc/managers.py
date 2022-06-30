from treebeard.mp_tree import MP_NodeQuerySet


class PublishedQueryset(MP_NodeQuerySet):
    def published(self):
        return self.filter(published=True)

    def draft(self):
        return self.filter(published=False)
