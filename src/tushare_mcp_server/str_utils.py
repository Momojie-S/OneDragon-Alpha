def is_subsequence(sub: str, main: str):
    """检查sub是否是main的子序列"""
    it = iter(main)
    return all(char in it for char in sub)
