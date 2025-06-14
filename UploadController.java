@RestController
public class UploadController {

    @PostMapping("/upload")
    public ResponseEntity<String> handleImageUpload(@RequestParam("image") MultipartFile file) throws IOException, InterruptedException {
        // Lưu file ảnh đầu vào
        String inputPath = "inference/input.jpg";
        String outputPath = "src/main/resources/static/result.jpg";
        file.transferTo(new File(inputPath));

        // Gọi script Python xử lý YOLO
        ProcessBuilder pb = new ProcessBuilder("python", "inference/detect.py", inputPath, outputPath);
        pb.inheritIO();
        Process process = pb.start();
        process.waitFor();

        return ResponseEntity.ok("/result.jpg");
    }
}
