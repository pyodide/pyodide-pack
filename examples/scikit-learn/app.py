from sklearn.tree import DecisionTreeClassifier  # noqa

est = DecisionTreeClassifier()
est.fit([[1], [2], [4]], [0, 1, 0])
