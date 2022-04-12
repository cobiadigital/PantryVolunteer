var wrapper = document.getElementById("signature-pad");
var clearButton = wrapper.querySelector("[data-action=clear]");


var canvas = wrapper.querySelector("canvas");
var signaturePad = new SignaturePad(canvas, {
  // It's Necessary to use an opaque color when saving image as JPEG;
  // this option can be omitted if only saving as PNG or SVG
  backgroundColor: 'rgb(255, 255, 255)'
});

function submitForm() {
    //Unterschrift in verstecktes Feld übernehmen
    document.getElementById('signature').value = signaturePad.toDataURL('image/svg+xml');
}

// Adjust canvas coordinate space taking into account pixel ratio,
// to make it look crisp on mobile devices.
// This also causes canvas to be cleared.
// function resizeCanvas() {
//     const ratio =  Math.max(window.devicePixelRatio || 1, 1);
//     canvas.width = canvas.offsetWidth * ratio;
//     canvas.height = canvas.offsetHeight * ratio;
//     canvas.getContext("2d").scale(ratio, ratio);
//     signaturePad.clear(); // otherwise isEmpty() might return incorrect value
// }
//
// window.addEventListener("resize", resizeCanvas);
// resizeCanvas();

clearButton.addEventListener("click", function (event) {
  signaturePad.clear();
});