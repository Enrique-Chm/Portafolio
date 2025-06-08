// Mostrar un mensaje en la consola (útil para depuración)
console.log("Hola pana!");

// Capturar un botón y hacer algo cuando se hace clic
document.querySelector("button").addEventListener("click", function() {
    alert("¡Botón presionado!");
});

// Cambiar el contenido de un elemento con ID "mensaje"
document.getElementById("mensaje").textContent = "Nuevo texto";

// Crear una función para reutilizar código
function sumar(a, b) {
    return a + b;
}

let resultado = sumar(5, 3); // Llama a la función y guarda el resultado
console.log(resultado); // Muestra "8" en la consola

// Temporizador: Ejecutar una función después de 3 segundos
setTimeout(function() {
    console.log("Han pasado 3 segundos");
}, 3000);

// Contador en tiempo real
let segundos = 0;
setInterval(function() {
    segundos++;
    console.log("Tiempo en la página: " + segundos + " segundos");
}, 1000);
