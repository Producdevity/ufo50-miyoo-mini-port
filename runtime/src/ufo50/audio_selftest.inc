/* Synthetic WAV fixtures exercise the real mixer without a playback device. */
#include "overlay_file_system.h"
int MaAudioSystem_runTests(const char* fixturePath) {
    DataWin data = {0};
    AudioGroup groups[3] = {0};
    Sound sounds[1] = {{.name="synthetic", .audioGroup=2, .audioFile=0,
        .flags=AUDIO_ENTRY_FLAG_IS_EMBEDDED, .volume=1, .pitch=1}};
    data.agrp.count=3; data.agrp.audioGroups=groups;
    data.sond.count=1; data.sond.sounds=sounds;
    data.lazyLoadAudio=true;
    MaAudioSystem* ma=MaAudioSystem_createOffline(&data);
    AudioSystem* audio=(AudioSystem*)ma;
    OverlayFileSystem* fs=OverlayFileSystem_create(fixturePath, fixturePath);
    maInit(audio, &data, (FileSystem*)fs);
    maGroupLoad(audio, 2);
    require(maGroupIsLoaded(audio, 2) && !maGroupIsLoaded(audio, 1));
    maGroupLoad(audio, 2);
    require(arrlen(audio->audioGroups)==3);
    /* Muted music layers must be silent from their first PCM buffer. */
    int32_t muted = maPlaySound(audio, 0, 100, true, 0.0f);
    require(muted >= SOUND_INSTANCE_ID_BASE && maIsPlaying(audio, muted));
    require(maGetSoundGain(audio, muted) == 0);
    float mutedPcm[1024]; ma_uint64 mutedRead = 0;
    require(ma_engine_read_pcm_frames(&ma->engine, mutedPcm, 512, &mutedRead) == MA_SUCCESS && mutedRead == 512);
    repeat(1024, i) require(mutedPcm[i] == 0);
    maSetSoundGain(audio, muted, 1, 0);
    require(maIsPlaying(audio, muted) && maGetSoundGain(audio, muted) == 1);
    maStopSound(audio, muted);
    sounds[0].volume = 0.5f;
    int32_t scaled = maPlaySound(audio, 0, 100, true, 0.4f);
    require(fabsf(maGetSoundGain(audio, scaled) - 0.2f) < 0.001f);
    maStopSound(audio, scaled);
    sounds[0].volume = 1;
    int32_t sound=maPlaySound(audio, 0, 0, true, 1.0f);
    require(sound>=SOUND_INSTANCE_ID_BASE);
    float pcm[1024]; ma_uint64 read=0;
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS && read==512);
    float energy=0; repeat(1024, i) energy+=pcm[i]*pcm[i];
    require(energy>1);
    MaAudioSystem_advanceOffline(ma, 0.05);
    require(ma->offlineFrames == 2205 && ma->offlineNonzero > 0 && ma->offlinePeak > 0);
    /* Old effect handles must not control music that reuses their mixer slot. */
    int32_t retired = sound;
    maStopSound(audio, retired);
    sound = maPlaySound(audio, 0, 100, true, 1.0f);
    require(sound != retired && maIsPlaying(audio, sound) && !maIsPlaying(audio, retired));
    maSetSoundGain(audio, retired, 0, 30);
    maSetSoundPitch(audio, retired, 2);
    maPauseSound(audio, retired);
    maResumeSound(audio, retired);
    maStopSound(audio, retired);
    maUpdate(audio, 0.05f);
    require(maIsPlaying(audio, sound) && maGetSoundGain(audio, sound) == 1);
    require(maGetSoundPitch(audio, sound) == 1);
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read) == MA_SUCCESS);
    energy = 0; repeat(1024, i) energy += pcm[i] * pcm[i]; require(energy > 1);

    maSetGroupGain(audio, 2, 0, 100);
    maUpdate(audio, 0.05f); require(fabsf(maGroupGain(ma, 2)-0.5f)<0.001f);
    maUpdate(audio, 0.05f); require(maGroupGain(ma, 2)==0);
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS);
    /* Miniaudio ramps volume changes; consume a buffer before checking silence. */
    require(ma_engine_read_pcm_frames(&ma->engine, pcm, 512, &read)==MA_SUCCESS);
    energy=0; repeat(1024, i) energy+=pcm[i]*pcm[i]; require(energy<0.0001f);
    /* Voice handles skip the stream namespace and never wrap to retired IDs. */
    maSetGroupGain(audio, 2, 1, 0);
    ma->nextInstanceCounter = AUDIO_STREAM_INDEX_BASE - 1;
    int32_t beforeStream = maPlaySound(audio, 0, 100, true, 1.0f);
    int32_t afterStream = maPlaySound(audio, 0, 100, true, 1.0f);
    require(beforeStream == AUDIO_STREAM_INDEX_BASE - 1);
    require(afterStream == AUDIO_STREAM_INDEX_BASE + MAX_AUDIO_STREAMS);
    maSetSoundGain(audio, afterStream, 0.4f, 0);
    maSetSoundPitch(audio, afterStream, 1.2f);
    require(fabsf(maGetSoundGain(audio, afterStream) - 0.4f) < 0.001f);
    require(fabsf(maGetSoundPitch(audio, afterStream) - 1.2f) < 0.001f);
    maStopSound(audio, beforeStream);
    require(!maIsPlaying(audio, beforeStream) && maIsPlaying(audio, afterStream));
    int32_t nextHandle = ma->nextInstanceCounter;
    ma->nextInstanceCounter = INT32_MAX;
    require(maPlaySound(audio, 0, 100, true, 1.0f) == -1 && maIsPlaying(audio, afterStream));
    ma->nextInstanceCounter = nextHandle;
    maGroupUnload(audio, 2);
    require(!maGroupIsLoaded(audio, 2) && !maIsPlaying(audio, sound));
    require(maPlaySound(audio, 0, 0, false, 1.0f)==-1);
    require(maGetSoundLength(audio, 0)==0);
    maDestroy(audio); OverlayFileSystem_destroy(fs);
    logInfo("Audio selftests passed: sparse groups, repeated load, nonzero stereo PCM, initial gain, silent first buffer, retired handles, stream boundary, group fades, unload safety\n");
    return 0;
}
