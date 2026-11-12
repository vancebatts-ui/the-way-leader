// Art-first Reel: full-bleed illustration with a slow push-in, the quote arriving over it.
// Usage: swift render_art.swift <dir> <art.png> <overlay.png> <score.m4a> <out.mp4>
import AVFoundation
import CoreGraphics
import ImageIO
import Foundation

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let args = Array(CommandLine.arguments[2...5])
let W = 1080, H = 1920, FPS: Int32 = 30
let duration = 12.0
let frameCount = Int(duration * Double(FPS))
let textIn = 0.5, textFull = 1.9      // the quote arrives between these seconds

func load(_ name: String) -> CGImage {
    let src = CGImageSourceCreateWithURL(dir.appendingPathComponent(name) as CFURL, nil)!
    return CGImageSourceCreateImageAtIndex(src, 0, nil)!
}
let art = load(args[0]), overlay = load(args[1])

let silentURL = dir.appendingPathComponent("silent.mp4")
try? FileManager.default.removeItem(at: silentURL)
let writer = try! AVAssetWriter(outputURL: silentURL, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: W, AVVideoHeightKey: H,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 9_000_000,
                                      AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel],
])
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: W, kCVPixelBufferHeightKey as String: H,
])
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

func ease(_ x: Double) -> Double { 0.5 - 0.5 * cos(Double.pi * min(max(x, 0), 1)) }

for f in 0..<frameCount {
    while !input.isReadyForMoreMediaData { usleep(2000) }
    var pb: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pb)
    let buf = pb!
    CVPixelBufferLockBaseAddress(buf, [])
    let ctx = CGContext(data: CVPixelBufferGetBaseAddress(buf), width: W, height: H, bitsPerComponent: 8,
                        bytesPerRow: CVPixelBufferGetBytesPerRow(buf), space: CGColorSpaceCreateDeviceRGB(),
                        bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
    ctx.interpolationQuality = .high
    let t = Double(f) / Double(FPS)
    let p = ease(Double(f) / Double(frameCount - 1))

    // the artwork pushes in slowly, 1.0 -> 1.065
    let s = 1.0 + 0.065 * p
    let aw = Double(W) * s, ah = Double(H) * s
    ctx.draw(art, in: CGRect(x: (Double(W) - aw) / 2, y: (Double(H) - ah) / 2, width: aw, height: ah))

    // the scrim and the quote arrive together, and then hold still
    let a = ease((t - textIn) / (textFull - textIn))
    if a > 0.001 {
        ctx.saveGState()
        ctx.setAlpha(CGFloat(a))
        ctx.draw(overlay, in: CGRect(x: 0, y: 0, width: Double(W), height: Double(H)))
        ctx.restoreGState()
    }

    // fade to black over the final second
    let fade = max(0.0, (t - (duration - 1.0)) / 1.0)
    if fade > 0 {
        ctx.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: fade))
        ctx.fill(CGRect(x: 0, y: 0, width: W, height: H))
    }
    CVPixelBufferUnlockBaseAddress(buf, [])
    adaptor.append(buf, withPresentationTime: CMTime(value: CMTimeValue(f), timescale: FPS))
}
input.markAsFinished()
let done = DispatchSemaphore(value: 0)
writer.finishWriting { done.signal() }
done.wait()
guard writer.status == .completed else { print("video write failed:", writer.error as Any); exit(1) }

// mux video + AAC score into the final file
let comp = AVMutableComposition()
let vAsset = AVURLAsset(url: silentURL), aAsset = AVURLAsset(url: dir.appendingPathComponent(args[2]))
let range = CMTimeRange(start: .zero, duration: CMTime(seconds: duration, preferredTimescale: 600))
let vt = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
let at = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
try! vt.insertTimeRange(range, of: vAsset.tracks(withMediaType: .video)[0], at: .zero)
try! at.insertTimeRange(range, of: aAsset.tracks(withMediaType: .audio)[0], at: .zero)

let outURL = dir.appendingPathComponent(args[3])
try? FileManager.default.removeItem(at: outURL)
let exp = AVAssetExportSession(asset: comp, presetName: AVAssetExportPresetPassthrough)!
exp.outputURL = outURL
exp.outputFileType = .mp4
let done2 = DispatchSemaphore(value: 0)
exp.exportAsynchronously { done2.signal() }
done2.wait()
guard exp.status == .completed else { print("export failed:", exp.error as Any); exit(1) }

// stills for a visual check: first frame, mid-fade, the cover frame, hold, fade-out
let gen = AVAssetImageGenerator(asset: AVURLAsset(url: outURL))
gen.requestedTimeToleranceBefore = .zero; gen.requestedTimeToleranceAfter = .zero
for s in [0.0, 1.2, 3.0, 7.0, 11.5] {
    let img = try! gen.copyCGImage(at: CMTime(seconds: s, preferredTimescale: 600), actualTime: nil)
    let u = dir.appendingPathComponent("\(outURL.deletingPathExtension().lastPathComponent)_still_\(Int(s * 10)).png")
    let d = CGImageDestinationCreateWithURL(u as CFURL, "public.png" as CFString, 1, nil)!
    CGImageDestinationAddImage(d, img, nil); CGImageDestinationFinalize(d)
}
print("wrote", outURL.path)
