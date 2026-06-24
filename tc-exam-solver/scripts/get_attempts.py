#!/usr/bin/env python3
"""
查询当前用户的考试记录（attempts）
用于检查是否有 in_progress 的未完成考试
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="生成获取考试记录的 JS 代码")
    args = parser.parse_args()

    js = r"""
(async () => {
  const token = localStorage.getItem('token');
  try {
    const resp = await fetch('/api/v1/my/attempts', {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    const attempts = Array.isArray(data) ? data : (data.data || data.attempts || []);
    const inProgress = attempts.filter(a => a.status === 'in_progress');
    return JSON.stringify({ attempts, in_progress: inProgress });
  } catch (e) {
    return JSON.stringify({ error: true, message: e.message });
  }
})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
