// Renders the Post 1 Reel: card slowly pushing in over a blurred parchment backdrop, then muxes score.m4a.
// Usage: swift render.swift <dir> [card.png bg.png score.m4a out.mp4]
import AVFoundation
import CoreGraphics
import ImageIO
import Foundation

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let args = CommandLine.arguments.count >= 6 ? Array(CommandLine.arguments[2...5])
    : ["card.png", "bg.png", "score.m4a", "WL-Post01-The-Calling-Reel.mp4"]
let W = 1080, H = 1920, FPS: Int32 = 30
let duration = 12.0
let frameCount = Int(duration * Double(FPS))

func load(_ name: String) -> CGImage {
    let src = CGImageSourceCreateWithURL(dir.appendingPathComponent(name) as CFURL, nil)!
    return CGImageSourceCreateImageAtIndex(src, 0, nil)!
}
let card = load(args[0]), bg = load(args[1])

let silentURL = dir.appendingPathComponent("silent.mp4")
try? FileManager.default.removeItem(at: silentURL)
let writer = try! AVAssetWriter(outputURL: silentURL, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264,
    AVVideoWidthKey: W, AVVideoHeightKey: H,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 8_000_000,
                                      AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel],
])
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: W, kCVPixelBufferHeightKey as String: H,
])
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

func ease(_ x: Double) -> Double { 0.5 - 0.5 * cos(Double.pi * x) }

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
    let p = ease(Double(f) / Double(frameCount - 1))

    // backdrop drifts in a touch for depth
    let bs = 1.0 + 0.03 * p
    let bw = Double(W) * bs, bh = Double(H) * bs
    ctx.draw(bg, in: CGRect(x: (Double(W) - bw) / 2, y: (Double(H) - bh) / 2, width: bw, height: bh))

    // the card pushes in from 960px to ~1030px wide
    let side = 960.0 * (1.0 + 0.075 * p)
    let rect = CGRect(x: (Double(W) - side) / 2, y: (Double(H) - side) / 2, width: side, height: side)
    ctx.saveGState()
    ctx.setShadow(offset: CGSize(width: 0, height: -10), blur: 40, color: CGColor(red: 0.12, green: 0.08, blue: 0.04, alpha: 0.55))
    ctx.draw(card, in: rect)
    ctx.restoreGState()

    // fade to black over the final second
    let t = Double(f) / Double(FPS)
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

// grab stills at 0s, 6s, 11.5s for a visual check
let gen = AVAssetImageGenerator(asset: AVURLAsset(url: outURL))
gen.requestedTimeToleranceBefore = .zero; gen.requestedTimeToleranceAfter = .zero
for s in [0.0, 6.0, 11.5] {
    let img = try! gen.copyCGImage(at: CMTime(seconds: s, preferredTimescale: 600), actualTime: nil)
    let u = dir.appendingPathComponent("\(outURL.deletingPathExtension().lastPathComponent)_still_\(Int(s * 10)).png")
    let d = CGImageDestinationCreateWithURL(u as CFURL, "public.png" as CFString, 1, nil)!
    CGImageDestinationAddImage(d, img, nil); CGImageDestinationFinalize(d)
}
print("wrote", outURL.path)
