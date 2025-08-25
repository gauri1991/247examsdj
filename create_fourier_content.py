#!/usr/bin/env python
"""
Generate enterprise-grade learning content for Fourier Transform concept
This demonstrates our AI-powered content generation capability!
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_portal.settings')
sys.path.insert(0, '/home/gss/Documents/projects/dts/test_platform')
django.setup()

from exams.models import (
    SyllabusNode, LearningContent, InteractiveElement, Assessment
)
from django.contrib.auth import get_user_model

User = get_user_model()

def create_fourier_learning_content():
    """Create comprehensive learning content for Fourier Transform"""
    
    # Find the Fourier Transform node
    try:
        fourier_node = SyllabusNode.objects.get(
            title="Fourier Transform and Properties"
        )
        print(f"Found node: {fourier_node.title}")
    except SyllabusNode.DoesNotExist:
        print("Fourier Transform node not found!")
        return
    
    # Get admin user for content creation
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # Clear existing content
    LearningContent.objects.filter(node=fourier_node).delete()
    print("Cleared existing content")
    
    # LEVEL 1: BASIC CONTENT
    basic_theory = LearningContent.objects.create(
        node=fourier_node,
        level='basic',
        content_type='theory',
        title="What is the Fourier Transform?",
        content="""
        <div class="learning-section">
            <h2>🎯 Learning Objectives</h2>
            <ul>
                <li>Understand what the Fourier Transform does</li>
                <li>Grasp the physical interpretation</li>
                <li>Learn the basic mathematical form</li>
                <li>Recognize real-world applications</li>
            </ul>
            
            <h2>📖 Introduction</h2>
            <p>The <strong>Fourier Transform</strong> is like a magical mathematical tool that can reveal the "hidden frequencies" inside any signal. Imagine you're listening to a complex piece of music - the Fourier Transform can tell you exactly which musical notes (frequencies) are being played at any moment!</p>
            
            <div class="key-insight">
                <h3>🔑 Key Insight</h3>
                <p><strong>Every signal is made up of simple waves!</strong> The Fourier Transform finds these simple wave components.</p>
            </div>
            
            <h2>🎼 Musical Analogy</h2>
            <p>Think of a piano chord:</p>
            <ul>
                <li><strong>Time Domain</strong>: You hear the complex chord sound</li>
                <li><strong>Frequency Domain</strong>: Fourier Transform reveals the individual notes (C, E, G)</li>
            </ul>
            
            <div class="math-box">
                <h3>📐 Mathematical Definition</h3>
                <p>For a continuous signal f(t), the Fourier Transform F(ω) is:</p>
                <div class="equation-center">
                    $$F(\\omega) = \\int_{-\\infty}^{\\infty} f(t) e^{-j\\omega t} dt$$
                </div>
                <p><strong>Where:</strong></p>
                <ul>
                    <li>F(ω) = Frequency domain representation</li>
                    <li>f(t) = Time domain signal</li>
                    <li>ω = Angular frequency (rad/s)</li>
                    <li>j = Imaginary unit (√-1)</li>
                    <li>e^(-jωt) = Complex exponential (Euler's formula)</li>
                </ul>
            </div>
            
            <h2>🌍 Real-World Applications</h2>
            <div class="applications-grid">
                <div class="app-item">
                    <h4>📱 Smartphone Audio</h4>
                    <p>MP3 compression uses Fourier analysis to remove frequencies you can't hear</p>
                </div>
                <div class="app-item">
                    <h4>🏥 Medical Imaging</h4>
                    <p>MRI and CT scans use Fourier transforms to create images from signals</p>
                </div>
                <div class="app-item">
                    <h4>📡 Communications</h4>
                    <p>WiFi, 4G/5G all use Fourier analysis for signal processing</p>
                </div>
                <div class="app-item">
                    <h4>🎵 Music Production</h4>
                    <p>Audio equalizers show frequency content using Fourier transforms</p>
                </div>
            </div>
            
            <h2>🎯 Quick Intuition Check</h2>
            <p>Before moving to the math, ask yourself:</p>
            <ol>
                <li>Can you think of the Fourier Transform as a "frequency detector"?</li>
                <li>Does it make sense that any signal can be made from simple waves?</li>
                <li>Can you imagine how this would be useful in engineering?</li>
            </ol>
        </div>
        """,
        estimated_read_time=10,
        order=1,
        created_by=admin_user,
        is_ai_generated=True,
        is_approved=True
    )
    
    # Basic Interactive Element
    basic_interactive = InteractiveElement.objects.create(
        content=basic_theory,
        element_type='slider_demo',
        title="Signal Composition Demo",
        description="See how complex signals are made from simple sine waves",
        config_data={
            "type": "fourier_synthesis",
            "frequencies": [1, 3, 5],
            "amplitudes": [1, 0.5, 0.3],
            "show_components": True,
            "show_sum": True
        },
        javascript_code="""
        // Interactive Fourier synthesis demonstration
        function createFourierDemo() {
            // Implementation for interactive demo
            console.log('Fourier synthesis demo initialized');
        }
        """,
        is_active=True
    )
    
    # Basic Assessment
    basic_assessment = Assessment.objects.create(
        content=basic_theory,
        question_type='mcq',
        schedule_type='immediate',
        question_text="What does the Fourier Transform convert a signal from?",
        question_data={
            "options": [
                "Frequency domain to time domain",
                "Time domain to frequency domain",
                "Analog to digital",
                "Continuous to discrete"
            ],
            "correct_answer": 1,
            "explanation": "The Fourier Transform converts signals from time domain (how amplitude changes over time) to frequency domain (what frequencies are present)."
        },
        max_points=10,
        difficulty_weight=1.0,
        is_active=True
    )
    
    # LEVEL 2: INTERMEDIATE CONTENT
    intermediate_theory = LearningContent.objects.create(
        node=fourier_node,
        level='intermediate',
        content_type='theory',
        title="Fourier Transform Properties",
        content="""
        <div class="learning-section">
            <h2>🎯 Learning Objectives</h2>
            <ul>
                <li>Master the key properties of Fourier Transform</li>
                <li>Understand how properties simplify calculations</li>
                <li>Apply properties to solve engineering problems</li>
                <li>Connect properties to physical interpretations</li>
            </ul>
            
            <h2>🔧 Essential Properties</h2>
            <p>The Fourier Transform has several powerful properties that make it incredibly useful in engineering. Think of these as "shortcuts" that make complex problems simple!</p>
            
            <div class="property-section">
                <h3>1️⃣ Linearity Property</h3>
                <div class="property-box">
                    <div class="property-math">
                        $$\\mathcal{F}\\{a \\cdot f(t) + b \\cdot g(t)\\} = a \\cdot F(\\omega) + b \\cdot G(\\omega)$$
                    </div>
                    <div class="property-explanation">
                        <h4>🧠 What it means:</h4>
                        <p>The Fourier Transform of a sum equals the sum of Fourier Transforms. This is like saying "the whole equals the sum of its parts."</p>
                        
                        <h4>🛠️ Engineering Application:</h4>
                        <p>When analyzing a complex signal made of multiple components, you can analyze each component separately and add the results!</p>
                        
                        <h4>📝 Example:</h4>
                        <p>If a signal = 3×sin(2πt) + 2×cos(4πt), you can find its Fourier Transform by taking:</p>
                        <p>FT{signal} = 3×FT{sin(2πt)} + 2×FT{cos(4πt)}</p>
                    </div>
                </div>
            </div>
            
            <div class="property-section">
                <h3>2️⃣ Time Shifting Property</h3>
                <div class="property-box">
                    <div class="property-math">
                        $$\\mathcal{F}\\{f(t - t_0)\\} = F(\\omega) \\cdot e^{-j\\omega t_0}$$
                    </div>
                    <div class="property-explanation">
                        <h4>🧠 What it means:</h4>
                        <p>Delaying a signal in time only changes the phase in frequency domain, not the magnitude!</p>
                        
                        <h4>🛠️ Engineering Application:</h4>
                        <p>This is crucial in communications - delays don't change what frequencies are present, only their timing relationships.</p>
                        
                        <h4>🎵 Audio Example:</h4>
                        <p>Playing the same song 2 seconds later has the same frequency content, just shifted in time.</p>
                    </div>
                </div>
            </div>
            
            <div class="property-section">
                <h3>3️⃣ Frequency Shifting Property</h3>
                <div class="property-box">
                    <div class="property-math">
                        $$\\mathcal{F}\\{f(t) \\cdot e^{j\\omega_0 t}\\} = F(\\omega - \\omega_0)$$
                    </div>
                    <div class="property-explanation">
                        <h4>🧠 What it means:</h4>
                        <p>Multiplying by a complex exponential shifts all frequencies by ω₀. This is the foundation of modulation!</p>
                        
                        <h4>🛠️ Engineering Application:</h4>
                        <p>This is how radio works! Your voice (low frequencies) gets shifted to radio frequencies for transmission.</p>
                        
                        <h4>📡 Radio Example:</h4>
                        <p>FM radio at 101.1 MHz takes your audio and shifts it up to that frequency for broadcast.</p>
                    </div>
                </div>
            </div>
            
            <div class="property-section">
                <h3>4️⃣ Scaling Property</h3>
                <div class="property-box">
                    <div class="property-math">
                        $$\\mathcal{F}\\{f(at)\\} = \\frac{1}{|a|} F\\left(\\frac{\\omega}{a}\\right)$$
                    </div>
                    <div class="property-explanation">
                        <h4>🧠 What it means:</h4>
                        <p>Compressing time expands frequency, and vice versa. There's an inverse relationship!</p>
                        
                        <h4>🛠️ Engineering Application:</h4>
                        <p>Fast events need high frequencies to represent them accurately. Slow events can be represented with low frequencies.</p>
                        
                        <h4>⚡ Pulse Example:</h4>
                        <p>A very narrow pulse (fast event) requires a very wide range of frequencies to represent it accurately.</p>
                    </div>
                </div>
            </div>
            
            <h2>🧮 Properties in Action: Problem Solving</h2>
            <div class="problem-example">
                <h3>📋 Example Problem</h3>
                <p><strong>Given:</strong> You know that FT{rect(t)} = sinc(ω)</p>
                <p><strong>Find:</strong> FT{3×rect(2t-4)}</p>
                
                <h4>🔧 Solution using properties:</h4>
                <ol>
                    <li><strong>Step 1:</strong> Factor out constants: 3×rect(2(t-2))</li>
                    <li><strong>Step 2:</strong> Apply scaling: FT{rect(2t)} = ½×sinc(ω/2)</li>
                    <li><strong>Step 3:</strong> Apply time shift: FT{rect(2(t-2))} = ½×sinc(ω/2)×e^(-j2ω)</li>
                    <li><strong>Step 4:</strong> Apply linearity: FT{3×rect(2(t-2))} = 3×½×sinc(ω/2)×e^(-j2ω)</li>
                    <li><strong>Answer:</strong> (3/2)×sinc(ω/2)×e^(-j2ω)</li>
                </ol>
            </div>
            
            <h2>🎯 Master Check</h2>
            <p>You've mastered this level when you can:</p>
            <ul>
                <li>✅ Identify which property to use for different signal transformations</li>
                <li>✅ Explain the physical meaning of each property</li>
                <li>✅ Solve problems using combinations of properties</li>
                <li>✅ Connect properties to real engineering applications</li>
            </ul>
        </div>
        """,
        estimated_read_time=15,
        order=1,
        created_by=admin_user,
        is_ai_generated=True,
        is_approved=True
    )
    
    # Intermediate Interactive Element
    intermediate_interactive = InteractiveElement.objects.create(
        content=intermediate_theory,
        element_type='graph',
        title="Property Visualizer",
        description="Interactive demonstration of Fourier Transform properties",
        config_data={
            "type": "property_demo",
            "properties": ["linearity", "time_shift", "frequency_shift", "scaling"],
            "real_time_update": True,
            "show_before_after": True
        },
        javascript_code="""
        // Interactive property demonstration
        function createPropertyDemo() {
            // Implementation for property visualization
            console.log('Property demo initialized');
        }
        """,
        is_active=True
    )
    
    # Intermediate Assessment
    intermediate_assessment = Assessment.objects.create(
        content=intermediate_theory,
        question_type='numerical',
        schedule_type='immediate',
        question_text="If F(ω) is the Fourier Transform of f(t), what is the Fourier Transform of f(3t-6)?",
        question_data={
            "expected_answer": "(1/3)*F(ω/3)*exp(-j*2*ω)",
            "tolerance": 0.1,
            "units": "",
            "hint": "Use scaling property first, then time shifting property",
            "solution_steps": [
                "Rewrite f(3t-6) as f(3(t-2))",
                "Apply scaling property: FT{f(3t)} = (1/3)F(ω/3)",
                "Apply time shift property: FT{f(3(t-2))} = (1/3)F(ω/3)×e^(-j2ω)"
            ]
        },
        max_points=15,
        difficulty_weight=1.5,
        is_active=True
    )
    
    # LEVEL 3: ADVANCED CONTENT
    advanced_theory = LearningContent.objects.create(
        node=fourier_node,
        level='advanced',
        content_type='theory',
        title="Advanced Fourier Analysis",
        content="""
        <div class="learning-section">
            <h2>🎯 Advanced Learning Objectives</h2>
            <ul>
                <li>Understand convolution and its Fourier relationship</li>
                <li>Master Parseval's theorem and energy conservation</li>
                <li>Apply Fourier analysis to system design</li>
                <li>Handle discontinuities and convergence issues</li>
            </ul>
            
            <h2>⚡ Convolution Theorem</h2>
            <div class="advanced-concept">
                <h3>🔥 The Most Powerful Property</h3>
                <div class="theorem-box">
                    <div class="theorem-math">
                        $$\\mathcal{F}\\{f(t) * g(t)\\} = F(\\omega) \\cdot G(\\omega)$$
                        $$\\mathcal{F}\\{f(t) \\cdot g(t)\\} = \\frac{1}{2\\pi} F(\\omega) * G(\\omega)$$
                    </div>
                    <p><strong>Translation:</strong> Convolution in time becomes multiplication in frequency!</p>
                </div>
                
                <h4>🛠️ Engineering Significance:</h4>
                <p>This theorem revolutionizes system analysis:</p>
                <ul>
                    <li><strong>Filter Design:</strong> Multiply frequency responses instead of convolving impulse responses</li>
                    <li><strong>Signal Processing:</strong> Design filters by specifying desired frequency response</li>
                    <li><strong>Communications:</strong> Analyze channel effects by multiplication</li>
                </ul>
                
                <div class="application-example">
                    <h4>📡 Real Application: Digital Filter Design</h4>
                    <p>To remove noise at 60Hz from an audio signal:</p>
                    <ol>
                        <li>Design frequency response H(ω) with notch at 60Hz</li>
                        <li>Output = FT⁻¹{Input_FT × H(ω)}</li>
                        <li>Much simpler than time-domain convolution!</li>
                    </ol>
                </div>
            </div>
            
            <h2>⚖️ Parseval's Theorem: Energy Conservation</h2>
            <div class="advanced-concept">
                <div class="theorem-box">
                    <div class="theorem-math">
                        $$\\int_{-\\infty}^{\\infty} |f(t)|^2 dt = \\frac{1}{2\\pi} \\int_{-\\infty}^{\\infty} |F(\\omega)|^2 d\\omega$$
                    </div>
                    <p><strong>Translation:</strong> Energy is conserved between time and frequency domains!</p>
                </div>
                
                <h4>🔋 Physical Interpretation:</h4>
                <ul>
                    <li><strong>Left side:</strong> Total energy of signal over all time</li>
                    <li><strong>Right side:</strong> Total energy distributed across all frequencies</li>
                    <li><strong>Meaning:</strong> Energy just gets redistributed, never lost!</li>
                </ul>
                
                <div class="application-example">
                    <h4>📊 Power Spectral Density</h4>
                    <p>|F(ω)|² tells you how much energy exists at each frequency - this is the foundation of spectral analysis used in:</p>
                    <ul>
                        <li>Audio engineering (equalizers)</li>
                        <li>Vibration analysis (machine health monitoring)</li>
                        <li>Astronomy (analyzing star light)</li>
                        <li>Medicine (EEG, ECG analysis)</li>
                    </ul>
                </div>
            </div>
            
            <h2>⚠️ Advanced Considerations</h2>
            
            <div class="warning-section">
                <h3>🚨 Convergence and Existence</h3>
                <p>Not all functions have Fourier Transforms! For existence, we need:</p>
                <div class="condition-box">
                    $$\\int_{-\\infty}^{\\infty} |f(t)| dt < \\infty$$
                </div>
                <p><strong>What this means:</strong> The function must be "absolutely integrable"</p>
                
                <h4>🔧 Engineering Workarounds:</h4>
                <ul>
                    <li><strong>Dirac Delta Functions:</strong> Handle impulses and constant signals</li>
                    <li><strong>Generalized Functions:</strong> Extend theory to periodic signals</li>
                    <li><strong>Windowing:</strong> Make non-integrable signals analyzable</li>
                </ul>
            </div>
            
            <div class="discontinuity-section">
                <h3>📈 Handling Discontinuities: Gibbs Phenomenon</h3>
                <p>When reconstructing signals with sharp edges:</p>
                <ul>
                    <li><strong>Problem:</strong> Oscillations appear near discontinuities</li>
                    <li><strong>Cause:</strong> Finite number of frequency components</li>
                    <li><strong>Solution:</strong> Windowing and apodization techniques</li>
                </ul>
                
                <div class="practical-tip">
                    <h4>💡 Practical Engineering Tip</h4>
                    <p>In digital signal processing, always consider:</p>
                    <ol>
                        <li>Sampling rate (Nyquist criterion)</li>
                        <li>Window functions for finite-length signals</li>
                        <li>Spectral leakage and resolution trade-offs</li>
                    </ol>
                </div>
            </div>
            
            <h2>🎯 Advanced Mastery Check</h2>
            <p>You've achieved advanced mastery when you can:</p>
            <ul>
                <li>✅ Design digital filters using frequency domain multiplication</li>
                <li>✅ Calculate signal energy using Parseval's theorem</li>
                <li>✅ Identify when Fourier Transform exists and suggest alternatives</li>
                <li>✅ Handle practical issues like aliasing and windowing</li>
                <li>✅ Connect theory to real engineering system design</li>
            </ul>
        </div>
        """,
        estimated_read_time=20,
        order=1,
        created_by=admin_user,
        is_ai_generated=True,
        is_approved=True
    )
    
    # Advanced Interactive Element
    advanced_interactive = InteractiveElement.objects.create(
        content=advanced_theory,
        element_type='code_editor',
        title="Fourier Transform Lab",
        description="Hands-on Python implementation and experimentation",
        config_data={
            "language": "python",
            "libraries": ["numpy", "matplotlib", "scipy"],
            "preloaded_code": "import numpy as np\nimport matplotlib.pyplot as plt\nfrom scipy.fft import fft, fftfreq",
            "exercises": [
                "Implement convolution using FFT",
                "Verify Parseval's theorem numerically",
                "Design a low-pass filter"
            ]
        },
        python_code="""
# Example: Convolution using FFT
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, ifft

def fft_convolution(x, h):
    # Zero-pad to avoid circular convolution
    N = len(x) + len(h) - 1
    x_padded = np.pad(x, (0, N - len(x)))
    h_padded = np.pad(h, (0, N - len(h)))
    
    # FFT, multiply, IFFT
    X = fft(x_padded)
    H = fft(h_padded)
    Y = X * H
    y = np.real(ifft(Y))
    
    return y

# Test the implementation
t = np.linspace(0, 1, 100)
x = np.sin(2*np.pi*5*t)  # 5 Hz sine wave
h = np.exp(-t*10)        # Exponential decay

# Convolution
y = fft_convolution(x, h)

# Plot results
plt.figure(figsize=(12, 4))
plt.subplot(131)
plt.plot(t, x)
plt.title('Input Signal x(t)')
plt.subplot(132)
plt.plot(t, h)
plt.title('Impulse Response h(t)')
plt.subplot(133)
plt.plot(y)
plt.title('Convolution y(t) = x(t)*h(t)')
plt.tight_layout()
plt.show()
        """,
        is_active=True
    )
    
    # Advanced Assessment
    advanced_assessment = Assessment.objects.create(
        content=advanced_theory,
        question_type='code_completion',
        schedule_type='spaced_1d',
        question_text="Complete the Python function to verify Parseval's theorem for a given signal:",
        question_data={
            "code_template": """
def verify_parseval(signal, dt):
    # Calculate time domain energy
    time_energy = np.sum(np.abs(signal)**2) * dt
    
    # Calculate frequency domain energy
    Signal_fft = fft(signal)
    N = len(signal)
    freq_energy = _____ # Complete this line
    
    return time_energy, freq_energy
            """,
            "expected_completion": "np.sum(np.abs(Signal_fft)**2) * dt / N",
            "test_cases": [
                {"input": "np.sin(2*np.pi*np.linspace(0,1,100))", "tolerance": 0.01}
            ]
        },
        max_points=20,
        difficulty_weight=2.0,
        is_active=True
    )
    
    print("✅ Successfully created comprehensive Fourier Transform learning content!")
    print(f"📚 Content created: {LearningContent.objects.filter(node=fourier_node).count()} pieces")
    print(f"🎮 Interactive elements: {InteractiveElement.objects.filter(content__node=fourier_node).count()}")
    print(f"❓ Assessments: {Assessment.objects.filter(content__node=fourier_node).count()}")
    
    return fourier_node

if __name__ == "__main__":
    create_fourier_learning_content()