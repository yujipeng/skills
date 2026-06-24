#!/usr/bin/env python3
"""
获取考试系列列表
调用 /api/v1/exams 接口，返回所有开放的考试系列
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="生成获取考试列表的 JS 代码")
    parser.parse_args()

    js = r"""
(async () => {
  const token = localStorage.getItem('token');
  try {
    const resp = await fetch('/api/v1/exams', {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    });
    const data = await resp.json();
    // 只返回 is_open=true 的考试
    const openExams = Array.isArray(data) ? data.filter(e => e.is_open) : (data.data || data.exams || data);
    return JSON.stringify({ exams: openExams, total: openExams.length });
  } catch (e) {
    return JSON.stringify({ error: true, message: e.message });
  }
})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
