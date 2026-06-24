#!/usr/bin/env python3
"""
检查登录状态
通过 localStorage 中的 JWT token 调用 /api/v1/auth/me 接口验证是否已登录
"""
import argparse

def main():
    parser = argparse.ArgumentParser(description="生成检查登录状态的 JS 代码")
    parser.parse_args()

    js = r"""
(async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    return JSON.stringify({ logged_in: false, reason: "no_token" });
  }
  try {
    const resp = await fetch('/api/v1/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (resp.status === 401 || resp.status === 403) {
      return JSON.stringify({ logged_in: false, reason: "token_invalid", status: resp.status });
    }
    const data = await resp.json();
    return JSON.stringify({ logged_in: true, user: data });
  } catch (e) {
    return JSON.stringify({ logged_in: false, reason: "error", message: e.message });
  }
})()
"""
    print(js.strip())

if __name__ == "__main__":
    main()
