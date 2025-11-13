import { useEffect } from 'react';

export default function Home() {
  useEffect(() => { window.location.replace('./stations/toc-s1/'); }, []);
  return null;
}
