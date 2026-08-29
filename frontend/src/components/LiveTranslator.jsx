import React from 'react';
import { TranscriptPanel } from './TranscriptPanel';
import { TranslationPanel } from './TranslationPanel';
import { EntityPanel } from './EntityPanel';

export function LiveTranslator({
  transcript,
  translation,
  sourceLang,
  targetLang,
  detectedLang,
  entities,
  warning,
  isOffline,
}) {
  return (
    <div className="deck-main">
      <div className="subtitles-deck">
        <TranscriptPanel
          transcript={transcript}
          sourceLang={sourceLang}
          detectedLang={detectedLang}
        />
        <TranslationPanel
          translation={translation}
          targetLang={targetLang}
          warning={warning}
          isOffline={isOffline}
        />
      </div>

      <EntityPanel entities={entities} />
    </div>
  );
}
