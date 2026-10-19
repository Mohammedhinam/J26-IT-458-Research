import React from 'react';

// Small local SVGs keep the demo independent of icon CDNs and network requests.
export default function Icon({name,size=22,...props}){
  const paths={
    tooth:<path d="M7 3C3 3 3 7 4 10c1 2 1 3 1 6 0 4 2 6 3 3l2-5c1-2 3-2 4 0l2 5c1 3 3 1 3-3 0-3 0-4 1-6 1-3 1-7-3-7-2 0-3 1-5 1S9 3 7 3Z"/>,
    image:<><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m4 17 5-5 4 4 3-3 5 5"/></>,
    questionnaire:<><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></>,
    feedback:<><path d="M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-8l-5 3v-3H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z"/><path d="m8 11 3 3 5-6"/></>,
    chart:<><path d="M3 3v18h18M7 17v-5M12 17V7M17 17V4"/></>,
    about:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></>,
    flask:<><path d="M9 3h6M10 3v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2L14 9V3M8 14h8"/></>,
    upload:<><path d="M12 16V3m-5 5 5-5 5 5M4 16v4h16v-4"/></>,
    play:<path d="m9 5 11 7-11 7Z"/>,
    close:<path d="m6 6 12 12M18 6 6 18"/>,
    check:<path d="m5 12 4 4L19 6"/>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]||paths.about}</svg>;
}
